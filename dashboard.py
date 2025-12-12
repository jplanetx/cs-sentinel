import streamlit as st
import pandas as pd
import gspread
import os
import plotly.express as px
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="CS Sentinel Dashboard", page_icon="🛡️", layout="wide")

# --- 1. SETUP & AUTH ---
# Load local .env if it exists
load_dotenv()

@st.cache_data(ttl=60)
def load_data():
    try:
        # PATH A: LOCAL MODE (Look for the file)
        if os.path.exists('credentials.json'):
            gc = gspread.service_account(filename='credentials.json')
            sheet_id = os.getenv("SHEET_ID")
            
        # PATH B: CLOUD MODE (Look for Streamlit Secrets)
        # We check if the 'gcp_service_account' section exists in secrets
        elif "gcp_service_account" in st.secrets:
            # We recreate the dictionary from the secrets
            creds_dict = st.secrets["gcp_service_account"]
            gc = gspread.service_account_from_dict(creds_dict)
            sheet_id = st.secrets["SHEET_ID"]
            
        else:
            st.error("❌ No credentials found! (Checked local 'credentials.json' and cloud secrets)")
            return pd.DataFrame()

        # Connect to Sheet
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

# --- 2. LOAD DATA ---
st.title("🛡️ CS Sentinel: Command Center")
st.markdown("### Autonomous Churn Prevention Agent")

df = load_data()

if not df.empty:
    # --- 3. METRICS ROW ---
    # Calculate key stats
    total_accounts = len(df)
    risk_accounts = len(df[df['Status'] == 'RISK'])
    sent_emails = len(df[df['Status'] == 'SENT'])
    
    # Create 3 columns for metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Accounts", total_accounts)
    col2.metric("⚠️ Accounts at Risk", risk_accounts, delta_color="inverse")
    col3.metric("✉️ Auto-Drafts Sent", sent_emails)
    
    st.divider()

    # --- 4. MAIN INTERFACE ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📋 Active Monitoring List")
        # Show a clean table of the data
        # We drop the heavy text columns for the summary view
        display_df = df[['Company Name', 'Last Login Date', 'Current MAU', 'Status', 'Unanswered Outreach Count']]
        st.dataframe(display_df, use_container_width=True)

    with col_right:
        st.subheader("📊 Risk Distribution")
        # Simple Pie Chart of Status
        if 'Status' in df.columns:
            fig = px.pie(df, names='Status', title='Portfolio Health', hole=0.4,
                         color_discrete_map={'HEALTHY':'#00CC96', 'RISK':'#EF553B', 'SENT':'#636EFA'})
            st.plotly_chart(fig, use_container_width=True)

    # --- 5. ACTION CENTER ---
    st.divider()
    st.subheader("🚨 Priority Action Items")
    
    # Filter for only RISK rows
    risk_rows = df[df['Status'] == 'RISK']
    
    if not risk_rows.empty:
        for index, row in risk_rows.iterrows():
            with st.expander(f"🔴 REVIEW: {row['Company Name']} (Ghosting Level: {row['Unanswered Outreach Count']})"):
                st.write(f"**Issue:** {row['Rescue Draft'].splitlines()[0] if row['Rescue Draft'] else 'No Draft'}")
                st.info(f"**Proposed Email Draft:**\n\n{row['Rescue Draft']}")
                st.button(f"Approve Action for {row['Company Name']}", key=f"btn_{index}")
    else:
        st.success("✅ No critical risks detected. System is monitoring.")

else:
    st.warning("No data found in the connected sheet.")