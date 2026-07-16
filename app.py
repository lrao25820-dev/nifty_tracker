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
def load_data():
    data = []
    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            current_price = info.last_price
            prev_close = info.previous_close
            pct_change = ((current_price - prev_close) / prev_close) * 100
            data.append({
                "Company": name,
                "Price (₹)": round(current_price, 2),
                "Change (%)": round(pct_change, 2)
            })
        except Exception:
            data.append({"Company": name, "Price (₹)": None, "Change (%)": None})
    return pd.DataFrame(data)

df = load_data()

# Display as live metric cards
cols = st.columns(6)
for idx, row in df.iterrows():
    if row["Price (₹)"] is not None:
        cols[idx].metric(
            label=row["Company"],
            value=f"₹{row['Price (₹)']}",
            delta=f"{row['Change (%)']}%"
        )

st.dataframe(df, use_container_width=True)
