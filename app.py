import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")
st.title("NIFTY 50 Top 5 Heavyweights")

# Tickers with .NS for National Stock Exchange
tickers = {
    "NIFTY 50": "^NSEI",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Reliance": "RELIANCE.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "L&T": "LT.NS"
}

# Auto-refresh every 10 seconds
@st.fragment(run_every=10)
def display_live_dashboard():
    # Create 6 columns side-by-side for your 6 stocks
    cols = st.columns(len(tickers))
    
    for idx, (name, ticker) in enumerate(tickers.items()):
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            current_price = info.last_price
            prev_close = info.previous_close
            
            # Calculate live percentage change
            pct_change = ((current_price - prev_close) / prev_close) * 100
            
            # Display each stock inside its own column layout
            with cols[idx]:
                st.metric(
                    label=name, 
                    value=f"₹{current_price:,.2f}", 
                    delta=f"{pct_change:+.2f}%"
                )
        except Exception:
            with cols[idx]:
                st.metric(label=name, value="Error", delta="N/A")

# Call the function to display the cards on your web page
display_live_dashboard()
