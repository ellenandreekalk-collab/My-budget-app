import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. Password Protection ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():
    st.stop()

# --- 2. Page Setup & Connection ---
st.set_page_config(page_title="Budget Master", page_icon="💰")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. Load Data ---
# Load transactions
try:
    existing_data = conn.read(worksheet="Sheet1", ttl="0")
    # Clean up empty rows/columns that Google Sheets sometimes adds
    existing_data = existing_data.dropna(subset=['Item', 'Cost'], how='all')
except:
    existing_data = pd.DataFrame(columns=["Date", "Item", "Cost"])

# Load monthly income from cell G1
try:
    income_sheet = conn.read(worksheet="Sheet1", usecols=[6], nrows=1, header=None)
    initial_income = float(income_sheet.iloc[0, 0])
except:
    initial_income = 3000.0

# Load recurring bills
try:
    bills_data = conn.read(worksheet="Bills", ttl="0")
    total_bills = bills_data['Amount'].sum()
except:
    total_bills = 1785.0  # Default fallback based on your records

# --- 4. Sidebar: Add Purchases & Income ---
with st.sidebar:
    st.header("📝 Log Purchase")
    with st.form("purchase_form", clear_on_submit=True):
        new_date = st.date_input("Date", datetime.now())
        new_item = st.text_input("Item Name")
        new_cost = st.number_input("Cost ($)", min_value=0.0, step=0.01)
        submit = st.form_submit_button("Add Purchase")

        if submit and new_item:
            new_row = pd.DataFrame([{"Date": new_date.strftime('%Y-%m-%d'), "Item": new_item, "Cost": new_cost}])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("Logged!")
            st.rerun()

    st.divider()
    st.header("⚙️ Monthly Income")
    starting_budget = st.number_input("Update Income ($)", value=initial_income, step=100.0)
    
    # Stable Income Update Logic
    if starting_budget != initial_income:
        income_df = pd.DataFrame([[starting_budget]])
        conn.update(worksheet="Sheet1", data=income_df, range="G1")
        st.rerun()

# --- 5. Calculations ---
total_spent = existing_data['Cost'].sum() if not existing_data.empty else 0.0
safe_to_spend = starting_budget - total_spent - total_bills
days_left = 31 - datetime.now().day
daily_allowance = safe_to_spend / days_left if days_left > 0 else safe_to_spend

# --- 6. Dashboard Display ---
st.title("💰 Budget Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Remaining Budget", f"${safe_to_spend:,.2f}")
col2.metric("Daily Allowance", f"${daily_allowance:,.2f}")
col3.metric("Total Bills", f"${total_bills:,.2f}")

st.divider()

st.subheader("📝 Transaction History")
if not existing_data.empty:
    st.dataframe(existing_data.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("No purchases logged yet.")
