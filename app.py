import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. పేజీ కాన్ఫిగరేషన్
st.set_page_config(layout="wide", page_title="Nifty 50 Dashboard")

st.title("📊 NIFTY 50 టాప్ 5 హెవీవెయిట్స్ అడ్వాన్స్డ్ డాష్‌బోర్డ్")
st.subheader("⚡ లైవ్ మార్కెట్ ఓవర్వ్యూ")

STOCKS = {
    'HDFC Bank': 'HDFCBANK.NS',
    'ICICI Bank': 'ICICIBANK.NS',
    'Reliance': 'RELIANCE.NS',
    'Bharti Airtel': 'BHARTIARTL.NS',
    'L&T': 'LT.NS'
}

WEIGHTS = {
    'HDFCBANK.NS': 0.33,
    'ICICIBANK.NS': 0.23,
    'RELIANCE.NS': 0.23,
    'BHARTIARTL.NS': 0.11,
    'LT.NS': 0.10
}

# 2. డేటా క్యాషింగ్
@st.cache_data(ttl=60)
def load_market_data():
    data_dict = {}
    for name, ticker in STOCKS.items():
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d", interval="5m")
        if not df.empty:
            data_dict[ticker] = df
    return data_dict

# 3. స్మార్ట్ రిఫ్రెష్ ఫ్రాగ్మెంట్
@st.fragment(run_every=5)
def render_dashboard():
    all_data = load_market_data()
    
    if not all_data or len(all_data) < len(STOCKS):
        st.warning("మార్కెట్ డేటాను సేకరిస్తోంది...")
        return

    common_index = None
    for ticker, df in all_data.items():
        if common_index is None:
            common_index = df.index
        else:
            common_index = common_index.intersection(df.index)
            
    for ticker in all_data:
        all_data[ticker] = all_data[ticker].loc[common_index]

    # --- Metrics Display ---
    cols = st.columns(len(STOCKS))
    for idx, (name, ticker) in enumerate(STOCKS.items()):
        if ticker in all_data:
            df = all_data[ticker]
            current_price = float(df['Close'].values[-1])
            prev_price = float(df['Close'].values[-2])
            price_change = current_price - prev_price
            pct_change = (price_change / prev_price) * 100
            
            with cols[idx]:
                st.metric(
                    label=name, 
                    value=f"₹{current_price:,.2f}", 
                    delta=f"{pct_change:+.2f}%"
                )

    st.markdown("---")
    st.subheader("🕯️ వెయిటెడ్ చార్ట్ & Buy/Sell కండిషనల్ సిగ్నల్స్")

    # --- Weighted Basket Calculation ---
    weighted_df = pd.DataFrame(index=common_index)
    weighted_df['Open'] = sum(all_data[ticker]['Open'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['High'] = sum(all_data[ticker]['High'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['Low'] = sum(all_data[ticker]['Low'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['Close'] = sum(all_data[ticker]['Close'] * WEIGHTS[ticker] for ticker in all_data)

    # EMA లెక్కింపు
    weighted_df['EMA_9'] = weighted_df['Close'].ewm(span=9, adjust=False).mean()
    weighted_df['EMA_21'] = weighted_df['Close'].ewm(span=21, adjust=False).mean()

    # Buy/Sell సిగ్నల్స్
    weighted_df['Signal'] = None
    weighted_df.loc[(weighted_df['EMA_9'] > weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) <= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Buy'
    weighted_df.loc[(weighted_df['EMA_9'] < weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) >= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Sell'

    # --- Plotly చార్ట్ ---
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=weighted_df.index,
        open=weighted_df['Open'],
        high=weighted_df['High'],
        low=weighted_df['Low'],
        close=weighted_df['Close'],
        name='Weighted Basket',
        increasing_line_color='#00cc66',
        decreasing_line_color='#ff3333'
    ))

    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_9'], name='9 EMA', line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_21'], name='21 EMA', line=dict(color='cyan', width=1.5)))

    buys = weighted_df[weighted_df['Signal'] == 'Buy']
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.999,
        mode='markers', name='Buy Signal',
        marker=dict(symbol='triangle-up', color='#00ff88', size=14, line=dict(width=1, color='white'))
    ))

    sells = weighted_df[weighted_df['Signal'] == 'Sell']
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.001,
        mode='markers', name='Sell Signal',
        marker=dict(symbol='triangle-down', color='#ff3344', size=14, line=dict(width=1, color='white'))
    ))

    fig.update_layout(
        yaxis_title="వెయిటెడ్ ధర (INR)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=480, 
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

render_dashboard()
