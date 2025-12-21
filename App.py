import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Proactive Budgeter", page_icon="📅")

# --- DATABASE INITIALIZATION ---
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'events' not in st.session_state:
    st.session_state.events = []

st.title("📅 Proactive Budget Countdown")

# --- SIDEBAR: GLOBAL SETTINGS ---
with st.sidebar:
    st.header("Monthly Setup")
    starting_budget = st.number_input("Starting Monthly Budget ($)", min_value=0, value=3000)
    st.divider()
    if st.button("Reset All Data"):
        st.session_state.expenses = []
        st.session_state.events = []
        st.rerun()

# --- SECTION 1: CALENDAR & PLANNING ---
st.subheader("🗓️ Upcoming Events")
with st.expander("Add a Future Event (Earmark Money)"):
    with st.form("event_form", clear_on_submit=True):
        event_name = st.text_input("Event Name (e.g., Mom's Birthday)")
        event_date = st.date_input("Event Date", min_value=datetime.today())
        event_cost = st.number_input("Set Aside Amount ($)", min_value=0.0)
        if st.form_submit_button("Earmark Funds"):
            st.session_state.events.append({"Event": event_name, "Date": event_date, "Amount": event_cost})

# --- SECTION 2: LOGGING ACTUAL SPENDING ---
st.subheader("💸 Log a Purchase")
with st.expander("Record an Expense"):
    with st.form("expense_form", clear_on_submit=True):
        item = st.text_input("What did you buy?")
        cost = st.number_input("Cost ($)", min_value=0.0)
        if st.form_submit_button("Log Expense"):
            st.session_state.expenses.append({"Item": item, "Cost": cost})

# --- SECTION 3: THE SMART COUNTDOWN ---
spent_so_far = sum(e['Cost'] for e in st.session_state.expenses)
earmarked_total = sum(ev['Amount'] for ev in st.session_state.events)
safe_to_spend = starting_budget - spent_so_far - earmarked_total

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.metric("Safe to Spend", f"${safe_to_spend:,.2f}", help="Starting budget minus spent AND earmarked money.")

with col2:
    st.metric("Actual Remaining", f"${starting_budget - spent_so_far:,.2f}", help="What's physically left in your bank.")

# --- SECTION 4: VISUAL REMINDERS ---
if st.session_state.events:
    st.write("### 🔔 Reminders")
    for ev in st.session_state.events:
        days_left = (ev['Date'] - datetime.today().date()).days
        st.info(f"**{ev['Event']}** is in {days_left} days. You've reserved **${ev['Amount']}**.")

# Progress Bar (based on Safe to Spend)
progress_val = max(0.0, min(1.0, (spent_so_far + earmarked_total) / starting_budget))
st.progress(progress_val)
