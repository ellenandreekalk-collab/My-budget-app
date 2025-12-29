import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection


# --- Password Protection ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["password"]}), key="password")
        return False
    return st.session_state["password_correct"]

if not check_password():

# 1. Page Setup
st.set_page_config(page_title="Budget Master", page_icon="💰")

# 2. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Load Data from Sheets
# Note: Ensure your sheet has headers: Date, Item, Cost
try:
    existing_data = conn.read(worksheet="Sheet1", ttl="0")
except:
    existing_data = pd.DataFrame(columns=["Date", "Item", "Cost"])

# 4. Initialize Memory for Calendar (Still temporary for the view)
if 'events' not in st.session_state:
    st.session_state.events = []

# --- GOOGLE CALENDAR LOGIC ---
def get_calendar_events():
    try:
        api_key = st.secrets["api_key"].strip()
        calendar_id = st.secrets["calendar_id"].strip()
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        params = {'key': api_key, 'timeMin': datetime.utcnow().isoformat() + 'Z'}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("items", [])
        return []
    except:
        return []
# --- Recurring Bills Logic ---
st.sidebar.subheader("🔁 Recurring Bills")

# Load existing bills from the "Bills" tab
try:
    bills_df = conn.read(worksheet="Bills")
except:
    # If tab doesn't exist yet, create a blank one
    bills_df = pd.DataFrame(columns=["Bill Name", "Amount"])

# Display and Edit Bills
with st.sidebar.expander("Edit Recurring Bills"):
    edited_bills = st.data_editor(bills_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Bill Changes"):
        conn.update(worksheet="Bills", data=edited_bills)
        st.success("Bills updated!")
        st.rerun()

# Calculate total bills to subtract from total budget
total_bills = edited_bills["Amount"].sum()
st.sidebar.info(f"Total Monthly Bills: ${total_bills:,.2f}")
st.title("💰 Smart Budget Countdown")

# 5. Math Logic (Using Data from the Google Sheet)
starting_budget = st.sidebar.number_input("Monthly Income", value=3000.0)
total_spent = existing_data["Cost"].sum()
safe_to_spend = starting_budget - total_spent - total_bills

# 6. Dashboard Metrics
st.info(f"You have logged **{len(existing_data)}** purchases.")
c1, c2 = st.columns(2)
c1.metric("Remaining Budget", f"${safe_to_spend:,.2f}")
c2.metric("Daily Allowance", f"${safe_to_spend/30:,.2f}")

# 7. Log Purchase (Saves to Google Sheets)

# Update your main budget calculation to include these bills
# (Find where you calculate remaining_budget and update it to:)
# remaining_budget = 3000 - total_spent - total_bills

# --- New Month / Clear Data Logic ---
with st.sidebar:
    st.divider()
    if st.button("🏁 Start New Month"):
        try:
            # 1. Read the current spending from Sheet1
            current_data = conn.read(worksheet="Sheet1")
            
            # 2. Create a name for the archive (e.g., "Dec 2025 Archive")
            archive_name = datetime.now().strftime("%b %Y Archive")
            
            # 3. Create a new tab and move the data there
            # Note: This requires the gsheets connection to have 'create' permissions
            conn.create(worksheet=archive_name, data=current_data)
            
            # 4. Clear Sheet1 by overwriting it with just the headers
            # This resets your "Remaining Budget" back to the full $3,000.00
            reset_df = pd.DataFrame(columns=["Item", "Cost", "Date"])
            conn.update(worksheet="Sheet1", data=reset_df)
            
            st.success(f"Budget reset! Data saved to {archive_name}")
            st.rerun()
        except Exception as e:
            st.error(f"Could not archive: {e}")
st.divider()
with st.form("buy_form", clear_on_submit=True):
    st.subheader("💸 Log New Purchase")
    item = st.text_input("Item Name")
    cost = st.number_input("Cost ($)", min_value=0.0)
    if st.form_submit_button("Save to Google Sheets"):
        new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Item": item, "Cost": cost}])
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Transaction Recorded!")
        st.rerun()

# 8. Calendar Sync
st.divider()
st.subheader("🗓️ Sync Calendar")
if st.button("🔄 Update Events"):
    fetched = get_calendar_events()
    # 1. Capture the start date/time
    events_list = [
        {
            "Name": e.get('summary', 'Event'),
            "Date": e.get('start', {}).get('dateTime', e.get('start', {}).get('date'))
        } for e in fetched
    ]
    
    # 2. ADD THIS LINE: Sort the list by the "Date" field
    st.session_state.events = sorted(events_list, key=lambda x: x['Date'])

for ev in st.session_state.events:
    if ev['Date']:
        # Formats the date to look like "Jan 03"
        clean_date = datetime.fromisoformat(ev['Date'].replace('Z', '+00:00')).strftime('%b %d')
        st.write(f"📍 {clean_date}: {ev['Name']}")
    else:
        st.write(f"📍 {ev['Name']}")
