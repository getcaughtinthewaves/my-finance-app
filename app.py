import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. SETUP & CONNECTION
st.set_page_config(page_title="Finance Cloud Tracker", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. LOAD DATA
# Reads the first tab (Portfolio) and the Budget tab
portfolio_df = conn.read(worksheet="Portfolio", ttl=0)
budget_df = conn.read(worksheet="Budget", ttl=0)

# FIX: Ensure 'Core' is boolean for the checkbox
if 'Core' in portfolio_df.columns:
    portfolio_df['Core'] = portfolio_df['Core'].astype(bool)

# Sidebar navigation
page = st.sidebar.selectbox("Choose Page", ["Dashboard", "Portfolio", "Budget"])

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
    
    if st.button("☁️ Save Portfolio to Cloud", key="save_portfolio"):
        conn.update(worksheet="Portfolio", data=edited_p)
        st.success("Portfolio synced with Google Sheets!")

# 4. BUDGET PAGE
elif page == "Budget":
    st.header("💰 Monthly Budget Tracker")
    
    # Simple editor for budget data
    edited_b = st.data_editor(budget_df, num_rows="dynamic")
    
    if st.button("☁️ Save Budget to Cloud", key="save_budget"):
        conn.update(worksheet="Budget", data=edited_b)
        st.success("Budget synced with Google Sheets!")

    # Visualizing Budget vs Actual
    if not budget_df.empty and 'Budgeted' in budget_df.columns and 'Actual' in budget_df.columns:
        st.subheader("Spending Analysis")
        fig_budget = px.bar(
            budget_df, 
            x='Category' if 'Category' in budget_df.columns else budget_df.index, 
            y=['Budgeted', 'Actual'], 
            barmode='group'
        )
        st.plotly_chart(fig_budget, use_container_width=True)

# 5. DASHBOARD PAGE
elif page == "Dashboard":
    st.header("📊 Live Net Worth Dashboard")
    
    stock_val = 0
    with st.spinner('Fetching live prices...'):
        try:
            usd_rate = yf.Ticker("CAD=X").fast_info['lastPrice']
            for _, row in portfolio_df.iterrows():
                if pd.isna(row['Ticker']) or row['Ticker'] == "": continue
                price = yf.Ticker(row['Ticker']).fast_info['lastPrice']
                v = price * row['Shares']
                if row.get('Currency') == 'USD': v *= usd_rate
                stock_val += v
            
            st.metric("Total Stock Value (CAD)", f"${stock_val:,.2f}")
            
            if not portfolio_df.empty:
                fig = px.pie(portfolio_df, values='Shares', names='Ticker', title="Asset Allocation")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Dashboard load error: {e}")
