import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

# పేజీ కాన్ఫిగరేషన్ సెటప్
st.set_page_config(layout="wide")
st.title("📊 NIFTY 50 టాప్ 5 హెవీవెయిట్స్ అడ్వాన్స్‌డ్ డ్యాష్‌బోర్డ్")

# 1. టిక్కర్ల వివరాలు
tickers = {
    "NIFTY 50": "^NSEI",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Reliance": "RELIANCE.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "L&T": "LT.NS"
}

# ఇమేజ్‌లో ఉన్న స్టాక్స్ మరియు వాటి వెయిటేజీలు
ticker_weights = {
    "HDFCBANK.NS": 11.48,
    "ICICIBANK.NS": 9.10,
    "RELIANCE.NS": 7.91,
    "LT.NS": 3.93,
    "BHARTIARTL.NS": 3.65
}

# వెయిటేజీలను నార్మలైజ్ చేయడం
total_weight = sum(ticker_weights.values())
normalized_weights = {ticker: w / total_weight for ticker, w in ticker_weights.items()}

# -------------------------------------------------------------------------
# 2. లైవ్ మార్కెట్ సెక్షన్ (ప్రти 5 సెకన్లకు రిఫ్రెష్ అవుతుంది)
st.subheader("⚡ లైవ్ మార్కెట్ ఓవర్‌వ్యూ")
cols = st.columns(len(tickers))

for idx, (name, ticker) in enumerate(tickers.items()):
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        current_price = info.last_price
        prev_close = info.previous_close
        
        pct_change = ((current_price - prev_close) / prev_close) * 100
        
        with cols[idx]:
            st.metric(
                label=name,
                value=f"₹{current_price:,.2f}",
                delta=f"{pct_change:+.2f}%"
            )
    except Exception:
        with cols[idx]:
            st.metric(label=name, value="డేటా ఎర్రర్", delta=None)

# -------------------------------------------------------------------------
# 3. వెయిటెడ్ క్యాండిల్‌స్టిక్ + Buy/Sell సిగ్నల్స్ సెక్షన్
st.markdown("---")
st.subheader("🕯️ వెయిటెడ్ చార్ట్ & Buy/Sell కండిషనల్ సిగ్నల్స్")

# సైడ్‌బార్‌లో చార్ట్ సెట్టింగ్స్
st.sidebar.header("🔧 చార్ట్ సెట్టింగ్స్")
interval = st.sidebar.selectbox(
    "టైమ్ ఇంటర్వల్ ఎంచుకోండి (Interval)", 
    ["5m", "10m", "15m", "1d", "1wk"], 
    index=3
)

if interval in ["5m", "10m", "15m"]:
    period = st.sidebar.selectbox("సమయ వ్యవధిని ఎంచుకోండి (Period)", ["1d", "5d", "1mo"], index=1)
else:
    period = st.sidebar.selectbox("సమయ వ్యవధిని ఎంచుకోండి (Period)", ["1mo", "3mo", "6mo", "1y"], index=1)

# హిస్టారికల్ డేటాను సేకరించే ఫంక్షన్
@st.cache_data(ttl=60)
def fetch_historical_data(stock_list, p, i):
    data = {}
    fetch_interval = "5m" if i == "10m" else i
    for t in stock_list:
        df = yf.download(t, period=p, interval=fetch_interval, progress=False)
        if not df.empty:
            if i == "10m":
                df = df.resample('10min').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
                }).dropna()
            data[t] = df
    return data

weight_tickers = list(ticker_weights.keys())
historical_data = fetch_historical_data(weight_tickers, period, interval)

if len(historical_data) == len(weight_tickers):
    # తేదీలను సమలేఖనం చేయడం
    common_index = historical_data[weight_tickers[0]].index
    for t in weight_tickers[1:]:
        common_index = common_index.intersection(historical_data[t].index)
    
    w_open = pd.Series(0.0, index=common_index)
    w_high = pd.Series(0.0, index=common_index)
    w_low = pd.Series(0.0, index=common_index)
    w_close = pd.Series(0.0, index=common_index)
    
    for t, weight in normalized_weights.items():
        df = historical_data[t].loc[common_index]
        w_open += df['Open'].squeeze() * weight
        w_high += df['High'].squeeze() * weight
        w_low += df['Low'].squeeze() * weight
        w_close += df['Close'].squeeze() * weight

    weighted_df = pd.DataFrame({'Open': w_open, 'High': w_high, 'Low': w_low, 'Close': w_close}, index=common_index)

    # 4. Buy/Sell కండిషన్స్ లెక్కించడం (EMA Crossover)
    weighted_df['EMA_Fast'] = weighted_df['Close'].ewm(span=9, adjust=False).mean()
    weighted_df['EMA_Slow'] = weighted_df['Close'].ewm(span=21, adjust=False).mean()
    
    # సిగ్నల్స్ గుర్తించడం
    weighted_df['Position'] = (weighted_df['EMA_Fast'] > weighted_df['EMA_Slow']).astype(int)
    weighted_df['Signal'] = weighted_df['Position'].diff()

    # Plotly క్యాండిల్‌స్టిక్ చార్ట్
    fig = go.Figure()

    # క్యాండిల్స్ జోడించడం (ఇక్కడ తప్పు సరిచేయబడింది)
    fig.add_trace(go.Candlestick(
        x=weighted_df.index,
        open=weighted_df['Open'], high=weighted_df['High'],
        low=weighted_df['Low'], close=weighted_df['Close'],
        name="Weighted Basket",
        increasing=dict(line=dict(color='#26a69a'), fillcolor='#26a69a'),
        decreasing=dict(line=dict(color='#ef5350'), fillcolor='#ef5350')
    ))

    # EMA లైన్స్ జోడించడం
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_Fast'], name='9 EMA (Fast)', line=dict(color='#2196F3', width=1.5)))
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_Slow'], name='21 EMA (Slow)', line=dict(color='#FF9800', width=1.5)))

    # Buy సిగ్నల్ మార్కర్స్ (ఆకుపచ్చ త్రికోణాలు)
    buys = weighted_df[weighted_df['Signal'] == 1]
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.998,
        mode='markers', name='Buy Signal',
        marker=dict(symbol='triangle-up', color='#00ff88', size=13, line=dict(color='white', width=1))
    ))

    # Sell సిగ్నల్ మార్కర్స్ (ఎрость త్రికోణాలు)
    sells = weighted_df[weighted_df['Signal'] == -1]
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.002,
        mode='markers', name='Sell Signal',
        marker=dict(symbol='triangle-down', color='#ff3333', size=13, line=dict(color='white', width=1))
    ))

    fig.update_layout(
        yaxis_title="వెయిటెడ్ ధర (INR)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=600,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("డేటాను సేకరిస్తోంది...")

# -------------------------------------------------------------------------
# 5. ఆటోమేటిక్ రిఫ్రెష్ లూప్ (5 సెకన్లు)
time.sleep(5)
st.rerun()
