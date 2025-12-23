import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. SETUP & CONNECTION
st.set_page_config(page_title="Finance Cloud Tracker", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

portfolio_df = conn.read(worksheet="Portfolio", ttl=0)
# 2. LOAD DATA
# ttl=0 ensures it doesn't "cache" old data; it checks the sheet every time
portfolio_df = conn.read(spreadsheet=SHEET_URL, worksheet="Portfolio", ttl=0)

# Sidebar
page = st.sidebar.selectbox("Choose Page", ["Dashboard", "Portfolio"])

# 3. PORTFOLIO PAGE
if page == "Portfolio":
    st.header("📈 TFSA Portfolio (Cloud)")
    
    col_setup = {
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Shares": st.column_config.NumberColumn("Shares", format="%.4f", step=0.0001),
        "Cost_Basis": st.column_config.NumberColumn("Avg Cost", format="$%.2f"),
        "Currency": st.column_config.SelectboxColumn("Currency", options=["CAD", "USD"]),
        "Core": st.column_config.CheckboxColumn("Core?")
    }

    edited_p = st.data_editor(portfolio_df, column_config=col_setup, num_rows="dynamic")
    
    if st.button("☁️ Save to Google Sheets", key="save_cloud_btn"):
        conn.update(spreadsheet=SHEET_URL, worksheet="Portfolio", data=edited_p)
        st.success("Synced with Google Sheets!")

# 4. DASHBOARD PAGE
elif page == "Dashboard":
    st.header("📊 Live Net Worth")
    
    stock_val = 0
    with st.spinner('Fetching live prices...'):
        try:
            usd_rate = yf.Ticker("CAD=X").fast_info['lastPrice']
            for _, row in portfolio_df.iterrows():
                if pd.isna(row['Ticker']): continue
                price = yf.Ticker(row['Ticker']).fast_info['lastPrice']
                v = price * row['Shares']
                if row['Currency'] == 'USD': v *= usd_rate
                stock_val += v
        except:
            st.error("Live price update failed.")

    st.metric("Total Stock Value (CAD)", f"${stock_val:,.2f}")
    
    if not portfolio_df.empty:
        fig = px.pie(portfolio_df, values='Shares', names='Ticker', title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)
