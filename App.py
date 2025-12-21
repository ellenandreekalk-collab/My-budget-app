import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. Page Setup
st.set_page_config(page_title="Budget Master", page_icon="💰")

# 2. Initialize App Memory (Session State)
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'events' not in st.session_state:
    st.session_state.events = []
if 'recurring' not in st.session_state:
    st.session_state.recurring = {}
if 'current_budget' not in st.session_state:
    st.session_state.current_budget = 3000.0

# --- GOOGLE CALENDAR LOGIC ---
def get_calendar_events():
    try:
        # Pulls from your Streamlit Secrets
        api_key = st.secrets["api_key"]
        calendar_id = st.secrets["calendar_id"]
        
        # URL to fetch events from a public calendar
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?key={api_key}"
        
        response = requests.get(url)
        data = response.json()
        
        if "items" in data:
            return data["items"]
        else:
            error_msg = data.get('error', {}).get('message', 'Unknown Error')
            st.error(f"Google says: {error_msg}")
            return []
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

st.title("💰 Smart Budget Countdown")

# 3. Sidebar (Income & Recurring Bills)
with st.sidebar:
    st.header("1. Monthly Budget")
    st.session_state.current_budget = st.number_input("Starting Amount", value=st.session_state.current_budget)
    
    st.divider()
    st.header("2. Recurring Bills")
    with st.expander("Add Fixed Bill"):
        b_name = st.text_input("Bill Name (e.g. Rent)")
        b_amt = st.number_input("Bill Amount", min_value=0.0)
        if st.button("Add Bill"):
            st.session_state.recurring[b_name] = b_amt
            st.rerun()

# 4. Math Logic
total_bills = sum(st.session_state.recurring.values())
total_spent = sum(e['Cost'] for e in st.session_state.expenses)
# Sum up anything user manually earmarked from the calendar
total_earmarked = sum(ev.get('Earmark', 0.0) for ev in st.session_state.events)

safe_to_spend = st.session_state.current_budget - total_bills - total_spent - total_earmarked

# 5. Dashboard Metrics
st.info(f"Fixed Bills Deducted: **${total_bills:,.2f}**")
c1, c2 = st.columns(2)
c1.metric("Safe to Spend", f"${safe_to_spend:,.2f}")
c2.metric("Daily Allowance", f"${safe_to_spend/30:,.2f}")

# 6. Calendar Sync Section
st.divider()
st.subheader("🗓️ Google Calendar Sync")
if st.button("🔄 Pull Upcoming Events"):
    fetched_events = get_calendar_events()
    if fetched_events:
        # Save fetched events to memory
        st.session_state.events = []
        for e in fetched_events:
            name = e.get('summary', 'Untitled Event')
            st.session_state.events.append({"Name": name, "Earmark": 0.0})
        st.success(f"Found {len(fetched_events)} events!")
    else:
        st.warning("No events found. Is the calendar public?")

# 7. Manual Entry Tabs
t1, t2 = st.tabs(["💸 Log Purchase", "🗓️ Earmark Events"])

with t1:
    with st.form("buy_form", clear_on_submit=True):
        item = st.text_input("Item Name")
        cost = st.number_input("Cost ($)", min_value=0.0)
        if st.form_submit_button("Log Spending"):
            st.session_state.expenses.append({"Item": item, "Cost": cost})
            st.rerun()

with t2:
    if st.session_state.events:
        for i, ev in enumerate(st.session_state.events):
            col1, col2 = st.columns([2, 1])
            col1.write(f"**{ev['Name']}**")
            new_amt = col2.number_input("Set aside $", min_value=0.0, key=f"ev_{i}")
            st.session_state.events[i]['Earmark'] = new_amt
        if st.button("Update Earmarks"):
            st.rerun()
    else:
        st.write("Click 'Pull Upcoming Events' above to see your calendar.")
