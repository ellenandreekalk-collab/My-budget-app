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

# --- 2. Connections ---
st.set_page_config(page_title="Budget App", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. Load Data ---
existing_data = conn.read(worksheet="Sheet1", ttl="0").dropna(subset=['Item', 'Cost'], how='all')
bills_data = conn.read(worksheet="Bills", ttl="0")

# Fetch initial income from Cell G1
try:
    income_df = conn.read(worksheet="Sheet1", usecols=[6], nrows=1, header=None)
    initial_income = float(income_df.iloc[0, 0])
except:
    initial_income = 3000.0

# --- 4. Sidebar ---
with st.sidebar:
    st.header("📝 Log Purchase")
    with st.form("purchase_form", clear_on_submit=True):
        new_date = st.date_input("Date", datetime.now())
        new_item = st.text_input("Item Name")
        new_cost = st.number_input("Cost ($)", min_value=0.0)
        if st.form_submit_button("Add Purchase") and new_item:
            new_row = pd.DataFrame([{"Date": new_date.strftime('%Y-%m-%d'), "Item": new_item, "Cost": new_cost}])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.rerun()

    st.divider()
    st.header("⚙️ Monthly Income")
    starting_budget = st.number_input("Update Income ($)", value=initial_income)
    
    # Stable update logic for G1
    if starting_budget != initial_income:
        new_income_df = pd.DataFrame([[starting_budget]])
        conn.update(worksheet="Sheet1", data=new_income_df, range="G1")
        st.rerun()

# --- 5. Calculations ---
total_spent = existing_data['Cost'].sum() if not existing_data.empty else 0.0
total_bills = bills_data['Amount'].sum() if not bills_data.empty else 0.0
safe_to_spend = starting_budget - total_spent - total_bills

# --- 6. Dashboard Main View ---
st.title("💰 Budget Dashboard")

col1, col2 = st.columns(2)
col1.metric("Remaining Budget", f"${safe_to_spend:,.2f}")
col2.metric("Total Bills", f"${total_bills:,.2f}")

st.divider()

# --- 7. The Missing Sections ---
tab1, tab2 = st.tabs(["📝 Purchase History", "📑 Recurring Bills"])

with tab1:
    st.subheader("Purchase History")
    # Only show relevant columns A, B, and C
    st.dataframe(existing_data[['Item', 'Cost', 'Date']], use_container_width=True)

with tab2:
    st.subheader("Your Monthly Bills")
    # Displays your Mortgage, CC Debt, and others from source [1]
    st.dataframe(bills_data, use_container_width=True)
