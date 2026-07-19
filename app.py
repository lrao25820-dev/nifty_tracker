import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. పేజీ కాన్ఫిగరేషన్ (మొబైల్ & వెబ్ స్క్రీన్స్ కోసం)
st.set_page_config(layout="wide", page_title="Nifty 50 Dashboard")[span_6](start_span)[span_6](end_span)

# యాప్ హెడర్స్
st.title("📊 NIFTY 50 టాప్ 5 హెవీవెయిట్స్ అడ్వాన్స్డ్ డాష్‌బోర్డ్")[span_7](start_span)[span_7](end_span)
st.subheader("⚡ లైవ్ మార్కెట్ ఓవర్వ్యూ")[span_8](start_span)[span_8](end_span)

# టాప్ 5 హెవీవెయిట్ స్టాక్స్ మరియు వాటి అంచనా వెయిటేజ్ (Weights)
STOCKS = {
    'HDFC Bank': 'HDFCBANK.NS',
    'ICICI Bank': 'ICICIBANK.NS',
    'Reliance': 'RELIANCE.NS',
    'Bharti Airtel': 'BHARTIARTL.NS',
    'L&T': 'LT.NS'
}[span_9](start_span)[span_9](end_span)

WEIGHTS = {
    'HDFCBANK.NS': 0.33,
    'ICICIBANK.NS': 0.23,
    'RELIANCE.NS': 0.23,
    'BHARTIARTL.NS': 0.11,
    'LT.NS': 0.10
}[span_10](start_span)[span_10](end_span)

# 2. డేటా క్యాషింగ్ (yf.Ticker ఉపయోగించి క్లీన్ డేటా పొందడం)
@st.cache_data(ttl=60)[span_11](start_span)[span_11](end_span)
def load_market_data():
    data_dict = {}
    for name, ticker in STOCKS.items():[span_12](start_span)[span_12](end_span)
        stock = yf.Ticker(ticker)[span_13](start_span)[span_13](end_span)
        # 5 రోజుల డేటాను 5 నిమిషాల ఇంట్రాడే ఇంటర్వెల్‌లో తెచ్చుకుంటుంది
        df = stock.history(period="5d", interval="5m")[span_14](start_span)[span_14](end_span)
        if not df.empty:
            data_dict[ticker] = df[span_15](start_span)[span_15](end_span)
    return data_dict[span_16](start_span)[span_16](end_span)

# 3. స్మార్ట్ రిఫ్రెష్ ఫ్రాగ్మెంట్ (ప్రతి 5 సెకన్లకు కేవలం ఈ భాగం మాత్రమే అప్‌డేట్ అవుతుంది)
@st.fragment(run_every=5)[span_17](start_span)[span_17](end_span)
def render_dashboard():
    all_data = load_market_data()[span_18](start_span)[span_18](end_span)
    
    if not all_data or len(all_data) < len(STOCKS):
        st.warning("డేటాను సేకరిస్తోంది లేదా మార్కెట్ డేటా సర్దుబాటు అవుతోంది...")[span_19](start_span)[span_19](end_span)
        return

    # --- టైమ్‌స్టాంప్ అలైన్‌మెంట్ బగ్ ఫిక్స్ ---
    # అన్ని స్టాక్స్‌లోనూ కామన్‌గా ఉన్న టైమింగ్స్ (Timestamps) మాత్రమే తీసుకుంటుంది
    common_index = None
    for ticker, df in all_data.items():[span_20](start_span)[span_20](end_span)
        if common_index is None:
            common_index = df.index
        else:
            common_index = common_index.intersection(df.index)
            
    # ఉమ్మడి టైమ్స్ ప్రకారం అన్ని డేటాఫ్రేమ్స్ ని రీ-ఇండెక్స్ చేయడం
    for ticker in all_data:[span_21](start_span)[span_21](end_span)
        all_data[ticker] = all_data[ticker].loc[common_index]

    # --- లైవ్ మార్కెట్ ఓవర్‌వ్యూ (Metrics Display) ---
    cols = st.columns(len(STOCKS))[span_22](start_span)[span_22](end_span)
    for idx, (name, ticker) in enumerate(STOCKS.items()):[span_23](start_span)[span_23](end_span)
        if ticker in all_data:[span_24](start_span)[span_24](end_span)
            df = all_data[ticker][span_25](start_span)[span_25](end_span)
            # .values వాడటం వల్ల సేఫ్ గా లాస్ట్ వాల్యూస్ ఫెచ్ అవుతాయి
            current_price = float(df['Close'].values[-1])[span_26](start_span)[span_26](end_span)
            prev_price = float(df['Close'].values[-2])[span_27](start_span)[span_27](end_span)
            price_change = current_price - prev_price[span_28](start_span)[span_28](end_span)
            pct_change = (price_change / prev_price) * 100[span_29](start_span)[span_29](end_span)
            
            with cols[idx]:[span_30](start_span)[span_30](end_span)
                st.metric(
                    label=name, 
                    value=f"₹{current_price:,.2f}", 
                    delta=f"{pct_change:+.2f}%"
                )[span_31](start_span)[span_31](end_span)

    st.markdown("---")[span_32](start_span)[span_32](end_span)
    st.subheader("🕯️ వెయిటెడ్ చార్ట్ & Buy/Sell కండిషనల్ సిగ్నల్స్")[span_33](start_span)[span_33](end_span)

    # --- వెయిటెడ్ బాస్కెట్ లెక్కింపు (Weighted Basket Calculation) ---
    weighted_df = pd.DataFrame(index=common_index)
    
    weighted_df['Open'] = sum(all_data[ticker]['Open'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['High'] = sum(all_data[ticker]['High'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['Low'] = sum(all_data[ticker]['Low'] * WEIGHTS[ticker] for ticker in all_data)
    weighted_df['Close'] = sum(all_data[ticker]['Close'] * WEIGHTS[ticker] for ticker in all_data)

    # --- పాండాస్_టిఎ బగ్ ఫిక్స్: నేటివ్ పాండాస్ తో EMA లెక్కింపు ---
    weighted_df['EMA_9'] = weighted_df['Close'].ewm(span=9, adjust=False).mean()[span_34](start_span)[span_34](end_span)
    weighted_df['EMA_21'] = weighted_df['Close'].ewm(span=21, adjust=False).mean()[span_35](start_span)[span_35](end_span)

    # Buy/Sell సిగ్నల్ లాజిక్ (9 EMA క్రాసింగ్ 21 EMA)
    weighted_df['Signal'] = None[span_36](start_span)[span_36](end_span)
    weighted_df.loc[(weighted_df['EMA_9'] > weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) <= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Buy[span_37](start_span)'[span_37](end_span)
    weighted_df.loc[(weighted_df['EMA_9'] < weighted_df['EMA_21']) & (weighted_df['EMA_9'].shift(1) >= weighted_df['EMA_21'].shift(1)), 'Signal'] = 'Sell[span_38](start_span)'[span_38](end_span)

    # --- Plotly చార్ట్ బిల్డింగ్ ---
    fig = go.Figure()[span_39](start_span)[span_39](end_span)

    # 1. వెయిటెడ్ బాస్కెట్ క్యాండిల్‌స్టిక్ చార్ట్
    fig.add_trace(go.Candlestick(
        x=weighted_df.index,
        open=weighted_df['Open'],[span_40](start_span)[span_40](end_span)
        high=weighted_df['High'],[span_41](start_span)[span_41](end_span)
        low=weighted_df['Low'],[span_42](start_span)[span_42](end_span)
        close=weighted_df['Close'],[span_43](start_span)[span_43](end_span)
        name='Weighted Basket',[span_44](start_span)[span_44](end_span)
        increasing_line_color='#00cc66',  # గ్రీన్ క్యాండిల్ బోర్డర్[span_45](start_span)[span_45](end_span)
        decreasing_line_color='#ff3333'   #  రెడ్ క్యాండిల్ బోర్డర్[span_46](start_span)[span_46](end_span)
    ))

    # 2. EMA లైన్స్ జోడించడం
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_9'], name='9 EMA (Fast)', line=dict(color='orange', width=1.5)))[span_47](start_span)[span_47](end_span)
    fig.add_trace(go.Scatter(x=weighted_df.index, y=weighted_df['EMA_21'], name='21 EMA (Slow)', line=dict(color='cyan', width=1.5)))[span_48](start_span)[span_48](end_span)

    # 3. Buy సిగ్నల్ మార్కర్స్ (ఆకుపచ్చ త్రికోణాలు)
    buys = weighted_df[weighted_df['Signal'] == 'Buy'][span_49](start_span)[span_49](end_span)
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.999,
        mode='markers', name='Buy Signal',[span_50](start_span)[span_50](end_span)
        marker=dict(symbol='triangle-up', color='#00ff88', size=14, line=dict(width=1, color='white'))[span_51](start_span)[span_51](end_span)
    ))

    # 4. Sell సిగ్నల్ మార్కర్స్ (ఎరుపు త్రికోణాలు)
    sells = weighted_df[weighted_df['Signal'] == 'Sell'][span_52](start_span)[span_52](end_span)
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.001,
        mode='markers', name='Sell Signal',[span_53](start_span)[span_53](end_span)
        marker=dict(symbol='triangle-down', color='#ff3344', size=14, line=dict(width=1, color='white'))[span_54](start_span)[span_54](end_span)
    ))

    # చార్ట్ లేఅవుట్ అప్‌డేట్ (మొబైల్ ఫ్రెండ్లీ సైజ్ & మార్జిన్స్)
    fig.update_layout(
        yaxis_title="వెయిటెడ్ ధర (INR)",[span_55](start_span)[span_55](end_span)
        xaxis_rangeslider_visible=False,[span_56](start_span)[span_56](end_span)
        template="plotly_dark",[span_57](start_span)[span_57](end_span)
        height=480,[span_58](start_span)[span_58](end_span)
        margin=dict(l=10, r=10, t=10, b=10),[span_59](start_span)[span_59](end_span)
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)[span_60](start_span)[span_60](end_span)
    )

    # యాప్‌లో చార్ట్ ప్రదర్శించడం
    st.plotly_chart(fig, use_container_width=True)[span_61](start_span)[span_61](end_span)

# యాప్ రన్ అవ్వడానికి ఫంక్షన్‌ని పిలవడం
render_dashboard()[span_62](start_span)[span_62](end_span)
