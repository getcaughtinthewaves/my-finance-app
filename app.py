import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. SETUP & CONNECTION
st.set_page_config(page_title="Finance Cloud Tracker", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. LOAD DATA
# This reads the "Portfolio" tab specifically
portfolio_df = conn.read(ttl=0)

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

    # This creates the editable table
    edited_p = st.data_editor(portfolio_df, column_config=col_setup, num_rows="dynamic")
    
    # IMPORTANT: This button MUST be indented under the "if page == 'Portfolio'" block
    if st.button("☁️ Save to Google Sheets", key="save_cloud_btn"):
        conn.update(worksheet="Portfolio", data=edited_p)
        st.success("Synced with Google Sheets!")

# 4. DASHBOARD PAGE
elif page == "Dashboard":
    st.header("📊 Live Net Worth")
    
    stock_val = 0
    with st.spinner('Fetching live prices...'):
        try:
            # Get current USD/CAD exchange rate
            usd_rate = yf.Ticker("CAD=X").fast_info['lastPrice']
            
            for _, row in portfolio_df.iterrows():
                if pd.isna(row['Ticker']) or row['Ticker'] == "": continue
                
                # Fetch live price from Yahoo Finance
                ticker_data = yf.Ticker(row['Ticker']).fast_info
                price = ticker_data['lastPrice']
                
                v = price * row['Shares']
                if row['Currency'] == 'USD': 
                    v *= usd_rate
                stock_val += v
        except Exception as e:
            st.error(f"Live price update failed: {e}")

    st.metric("Total Stock Value (CAD)", f"${stock_val:,.2f}")
    
    if not portfolio_df.empty:
        fig = px.pie(portfolio_df, values='Shares', names='Ticker', title="Portfolio Allocation")
        st.plotly_chart(fig, use_container_width=True)
