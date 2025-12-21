import streamlit as st
import pandas as pd
from datetime import datetime, date

# 1. Page Configuration
st.set_page_config(page_title="Proactive Budgeter", page_icon="💰")

# 2. Initialize Memory (Session State)
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'events' not in st.session_state:
    st.session_state.events = []
if 'recurring' not in st.session_state:
    st.session_state.recurring = {} # Store as {Name: Amount}
if 'current_budget' not in st.session_state:
    st.session_state.current_budget = 3000.0

st.title("💰 Smart Budget Countdown")

# 3. Sidebar: Setup & Recurring Bills
with st.sidebar:
    st.header("1. Monthly Budget")
    new_budget = st.number_input("Total Monthly Income/Start", min_value=0.0, value=st.session_state.current_budget)
    if st.button("Save Budget"):
        st.session_state.current_budget = new_budget
        st.rerun()
    
    st.divider()
    st.header("2. Recurring Bills")
    with st.expander("Add Monthly Bill"):
        bill_name = st.text_input("Bill Name (e.g. Rent)")
        bill_amt = st.number_input("Monthly Amount", min_value=0.0, key="bill_val")
        if st.button("Add Bill"):
            if bill_name and bill_amt > 0:
                st.session_state.recurring[bill_name] = bill_amt
                st.rerun()
    
    # Show list of bills with a way to clear them
    if st.session_state.recurring:
        for name, amt in st.session_state.recurring.items():
            st.caption(f"✅ {name}: ${amt:,.2f}")
        if st.button("Clear All Bills"):
            st.session_state.recurring = {}
            st.rerun()

    st.divider()
    if st.button("RESET ALL DATA", type="primary"):
        st.session_state.expenses = []
        st.session_state.events = []
        st.session_state.recurring = {}
        st.rerun()

# 4. Math Logic
today = date.today()
days_in_month = 30 # Simplified
days_left = max(1, days_in_month - today.day)

total_fixed_costs = sum(st.session_state.recurring.values())
total_spent = sum(e['Cost'] for e in st.session_state.expenses)
total_earmarked = sum(ev['Amount'] for ev in st.session_state.events)

# The Countdown Formula
actual_starting_money = st.session_state.current_budget - total_fixed_costs
safe_to_spend = actual_starting_money - total_spent - total_earmarked
daily_allowance = safe_to_spend / days_left

# 5. Dashboard Metrics
st.info(f"Fixed Bills Deducted: **${total_fixed_costs:,.2f}**")
c1, c2 = st.columns(2)
c1.metric("Safe to Spend", f"${safe_to_spend:,.2f}")
c2.metric("Daily Allowance", f"${daily_allowance:,.2f}")

prog_val = max(0.0, min(1.0, (total_spent + total_earmarked + total_fixed_costs) / st.session_state.current_budget)) if st.session_state.current_budget > 0 else 0
st.progress(prog_val)

# 6. Entry Tabs
t1, t2 = st.tabs(["💸 Log Spending", "🗓️ Future Events"])

with t1:
    with st.form("exp_form", clear_on_submit=True):
        item = st.text_input("Item Name")
        cat = st.selectbox("Category", ["Food", "Fun", "Transport", "Shopping", "Other"])
        cost = st.number_input("Cost ($)", min_value=0.0)
        if st.form_submit_button("Log"):
            if item and cost > 0:
                st.session_state.expenses.append({"Item": item, "Cost": cost, "Category": cat})
                st.rerun()

with t2:
    with st.form("evt_form", clear_on_submit=True):
        e_name = st.text_input("Event")
        e_date = st.date_input("Date")
        e_cost = st.number_input("Set Aside ($)", min_value=0.0)
        if st.form_submit_button("Earmark"):
            if e_name and e_cost > 0:
                st.session_state.events.append({"Event": e_name, "Date": e_date, "Amount": e_cost})
                st.rerun()

# 7. Recent History
if st.session_state.expenses:
    st.write("### Recent Expenses")
    st.table(pd.DataFrame(st.session_state.expenses).tail(5))
