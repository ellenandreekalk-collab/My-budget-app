import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Budget Countdown", page_icon="💰", layout="centered")

# 2. Initialize "Memory" (Session State)
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'events' not in st.session_state:
    st.session_state.events = []
if 'current_budget' not in st.session_state:
    st.session_state.current_budget = 3000.0

st.title("💰 Budget Countdown")

# 3. Sidebar: Adjustments & Settings
with st.sidebar:
    st.header("Monthly Setup")
    # This input lets you change your starting amount
    new_budget = st.number_input("Starting Budget ($)", min_value=0.0, value=st.session_state.current_budget)
    
    if st.button("Save New Budget"):
        st.session_state.current_budget = new_budget
        st.success("Budget Updated!")
        st.rerun()
    
    st.divider()
    # Reset button to clear everything
    if st.button("Reset All Data"):
        st.session_state.expenses = []
        st.session_state.events = []
        st.rerun()

# Reference the budget for our math
starting_budget = st.session_state.current_budget

# 4. Input Sections (Tabs work great on mobile)
tab1, tab2 = st.tabs(["💸 Log Expense", "🗓️ Earmark Event"])

with tab1:
    with st.form("expense_form", clear_on_submit=True):
        item = st.text_input("What did you buy?")
        cost = st.number_input("Cost ($)", min_value=0.0, step=1.0)
        if st.form_submit_button("Log Expense"):
            if item and cost > 0:
                st.session_state.expenses.append({"Item": item, "Cost": cost, "Type": "Spent"})
                st.rerun()

with tab2:
    with st.form("event_form", clear_on_submit=True):
        e_name = st.text_input("Event Name (e.g. Concert)")
        e_date = st.date_input("When is it?", min_value=datetime.today())
        e_cost = st.number_input("Amount to set aside ($)", min_value=0.0, step=1.0
