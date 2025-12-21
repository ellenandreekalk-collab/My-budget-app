import streamlit as st
import pandas as pd
from datetime import datetime, date
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# 1. Page Setup
st.set_page_config(page_title="Budget Master", page_icon="💰")

# 2. Initialize App Memory
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
        # Pulls from your saved Streamlit Secrets
        creds_info = st.secrets["google_credentials"]
        # Note: For a true automated sync, a Refresh Token is usually needed. 
        # This setup will allow the app to authenticate using your Client Secret.
        service = build('calendar', 'v3', developerKey=creds_info['client_id'])
        
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        return events_result.get('items', [])
    except Exception as e:
        st.error(f"Sync Error: Ensure your Calendar is public or shared with the Client Email.")
        return []

st.title("💰 Smart Budget Countdown")

# 3. Sidebar (Income & Recurring Bills)
with st.sidebar:
    st.header("1. Monthly Budget")
    st.session_state.current_budget = st.number_input("Starting Amount", value=st.session_state.current_budget)
    
    st.divider()
    st.header("2. Recurring Bills")
    with st.expander("Add Bill"):
        b_name = st.text_input("Name")
        b_amt = st.number_input("Amount", min_value=0.0)
        if st.button("Add Bill"):
            st.session_state.recurring[b_name] = b_amt
            st.rerun()

# 4. Math Logic
total_bills = sum(st.session_state.recurring.values())
total_spent = sum(e['Cost'] for e in st.session_state.expenses)
total_earmarked = sum(ev['Amount'] for ev in st.session_state.events)
safe_to_spend = st.session_state.current_budget - total_bills - total_spent - total_earmarked

# 5. Dashboard Metrics
st.info(f"Fixed Bills Deducted: **${total_bills:,.2f}**")
c1, c2 = st.columns(2)
c1.metric("Safe to Spend", f"${safe_to_spend:,.2f}")
c2.metric("Daily Allowance", f"${safe_to_spend/30:,.2f}")

# 6. Calendar Sync 

def get_calendar_events():
    try:
        api_key = st.secrets["api_key"]
        calendar_id = st.secrets["calendar_id"]
        
        # This uses a simple web request instead of the heavy Google library
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?key={api_key}"
        
        import requests
        response = requests.get(url)
        data = response.json()
        
        if "items" in data:
            return data["items"]
        else:
            st.error(f"Google says: {data.get('error', {}).get('message', 'Unknown Error')}")
            return []
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return []

# 7. Manual Entry Tabs
t1, t2 = st.tabs(["💸 Log Purchase", "🗓️ Earmark Event"])
with t1:
    with st.form("buy_form", clear_on_submit=True):
        item = st.text_input("Item")
        cost = st.number_input("Cost", min_value=0.0)
        if st.form_submit_button("Log"):
            st.session_state.expenses.append({"Item": item, "Cost": cost})
            st.rerun()
