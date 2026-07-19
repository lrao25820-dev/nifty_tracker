import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. పేజీ కాన్ఫిగరేషన్ (మొబైల్ & వెబ్ స్క్రీన్స్ కోసం)
st.set_page_config(layout="wide", page_title="Nifty 50 Dashboard")

# యాప్ హెడర్స్
st.title("📊 NIFTY 50 టాప్ 5 హెవీవెయిట్స్ అడ్వాన్స్డ్ డాష్‌బోర్డ్")
st.subheader("⚡ లైవ్ మార్కెట్ ఓవర్వ్యూ")

# టాప్ 5 హెవీవెయిట్ స్టాక్స్ మరియు వాటి అంచనా వెయిటేజ్ (Weights)
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

# 2. డేటా క్యాషింగ్ (ఫాస్ట్ లోడింగ్ కోసం మరియు API బ్లాక్ అవ్వకుండా ఉండటానికి)
@st.cache_data(ttl=60)
def load_market_data():
    data_dict = {}
    for name, ticker in STOCKS.items():
        # 5 రోజుల డేటాను 5 నిమిషాల ఇంట్రాడే ఇంటర్వెల్‌లో తెచ్చుకుంటుంది
        df = yf.download(ticker, period="5d", interval="5m")
        if not df.empty:
            data_dict[ticker] = df
    return data_dict

# 3. స్మార్ట్ రిఫ్రెష్ ఫ్రాగ్మెంట్ (ప్రతి 5 సెకన్లకు కేవలం ఈ భాగం మాత్రమే అప్‌డేట్ అవుతుంది)
@st.fragment(run_every=5)
def render_dashboard():
    all_data = load_market_data()
    
    if not all_data:
        st.warning("డేటాను సేకరిస్తోంది...")
        return

    # --- లైవ్ మార్కెట్ ఓవర్‌వ్యూ (Metrics Display) ---
    cols = st.columns(len(STOCKS))
    for idx, (name, ticker) in enumerate(STOCKS.items()):
        if ticker in all_data:
            df = all_data[ticker]
            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
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

    # --- వెయిటెడ్ బాస్కెట్ లెక్కింపు (Weighted Basket Calculation) ---
    weighted_df = pd.DataFrame()
    
    for ticker, df in all_data.items():
        if weighted_df.empty:
            weighted_df.index = df.index
            weighted_df['Open'] = df['Open'] * WEIGHTS[ticker]
            weighted_df['High'] = df['High'] * WEIGHTS[ticker]
            weighted_df['Low'] = df['Low'] * WEIGHTS[ticker]
            weighted_df['Close'] = df['Close'] * WEIGHTS[ticker]
        else:
            weighted_df['Open'] += df['Open'] * WEIGHTS[ticker]
            weighted_df['High'] += df['High'] * WEIGHTS[ticker]
            weighted_df['Low'] += df['Low'] * WEIGHTS[ticker]
            weighted_df['Close'] += df['Close'] * WEIGHTS[ticker]

    # EMA ఇండికేటర్స్ లెక్కించడం
    weighted_df['EMA_9'] = ta.ema(weighted_df['Close'], length=9)
    weighted_df['EMA_21'] = ta.ema(weighted_df['Close'], length=21)

    # Buy/Sell సిగ్నల్ లాజిక్ (9 EMA క్రాసింగ్ 21 EMA)
    weighted_df['Signal'] = None
    weighted_df.loc[(weighted_df['EMA_9'] > weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) <= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Buy'
    weighted_df.loc[(weighted_df['EMA_9'] < weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) >= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Sell'

    # --- Plotly చార్ట్ బిల్డింగ్ ---
    fig = go.Figure()

    # 1. వెయిటెడ్ బాస్కెట్ క్యాండిల్‌స్టిక్ చార్ట్ (ఇక్కడ క్యాండిల్స్ యాడ్ చేశాం)
    fig.add_trace(go.Candlestick(
        x=weighted_df.index,
        open=weighted_df['Open'],
        high=weighted_df['High'],
        low=weighted_df['Low'],
        close=weighted_df['Close'],
        name='Weighted Basket',
        increasing_line_color='#00cc66',  # గ్రీన్ క్యాండిల్ బోర్డర్
        decreasing_line_color='#ff3333'   # రెడ్ క్యాండిల్ బోర్డర్
    ))

    # 2. EMA లైన్స్ జోడించడం
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_9'], name='9 EMA (Fast)', line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_21'], name='21 EMA (Slow)', line=dict(color='cyan', width=1.5)))

    # 3. Buy సిగ్నల్ మార్కర్స్ (ఆకుపచ్చ త్రికోణాలు)
    buys = weighted_df[weighted_df['Signal'] == 'Buy']
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.998,
        mode='markers', name='Buy Signal',
        marker=dict(symbol='triangle-up', color='#00ff88', size=14, line=dict(width=1, color='white'))
    ))

    # 4. Sell సిగ్నల్ మార్కర్స్ (ఎరుపు త్రికోణాలు)
    sells = weighted_df[weighted_df['Signal'] == 'Sell']
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.002,
        mode='markers', name='Sell Signal',
        marker=dict(symbol='triangle-down', color='#ff3344', size=14, line=dict(width=1, color='white'))
    ))

    # చార్ట్ లేఅవుట్ అప్‌డేట్ (మొబైల్ ఫ్రెండ్లీ సైజ్ & మార్జిన్స్)
    fig.update_layout(
        yaxis_title="వెయిటెడ్ ధర (INR)",
        xaxis_rangeslider_visible=False, # క్లీన్ లుక్ కోసం కింద ఉండే రేంజ్ స్లైడర్ తీసేశాం
        template="plotly_dark",
        height=500,  # మొబైల్ స్క్రీన్‌లలో పర్ఫెక్ట్‌గా ఫిట్ అవ్వడానికి హైట్ అడ్జస్ట్ చేశాం
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # యాప్‌లో చార్ట్ ప్రదర్శించడం
    st.plotly_chart(fig, use_container_width=True)

# యాప్ రన్ అవ్వడానికి ఫంక్షన్‌ని పిలవడం
render_dashboard()
