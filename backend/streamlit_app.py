import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import os
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="KRYPTOS Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS INJECTION FOR PREMIUM DARK MODE ---
st.markdown("""
    <style>
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        background-color: #151a23;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .metric-title { color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 600;}
    .metric-value { color: #f0f2f5; font-size: 2.5rem; font-weight: 700; }
    .metric-sub { color: #94a3b8; font-size: 0.75rem; margin-top: 0.5rem; }
    
    .stDataFrame { border: 1px solid #2d3748; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- API HELPERS ---
try:
    API_BASE_URL = st.secrets["API_BASE_URL"]
except Exception:
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

@st.cache_data(ttl=60)
def fetch_dashboard_data():
    try:
        # Increased timeout to 60s to account for Render free-tier cold starts
        res = requests.get(f"{API_BASE_URL}/api/dashboard", timeout=60)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        return {"status": "error", "message": f"Connection Refused: {str(e)}"}
    return None

@st.cache_data(ttl=60)
def fetch_history_data(symbol):
    try:
        res = requests.get(f"{API_BASE_URL}/api/history/{symbol}", timeout=60)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        return None
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_candlestick_data_yfinance(symbol):
    yf_symbol = f"{symbol.upper().strip()}-USD"
    df = yf.download(yf_symbol, period="7d", interval="1h", progress=False)
    
    if df.empty:
        raise Exception(f"No candlestick data found for {yf_symbol}")
        
    # Handle multi-index columns on newer yfinance versions
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    df.reset_index(inplace=True)
    
    # yfinance sometimes outputs Datetime or Date
    time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
    df.rename(columns={time_col: 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'}, inplace=True)
    return df.to_dict('records')

# --- MAIN RENDER ---
def main():
    st.markdown(
        "<h1 style='background: linear-gradient(90deg, #60a5fa, #3b82f6, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>KRYPTOS Intelligence</h1>", 
        unsafe_allow_html=True
    )
    st.markdown("<p style='color: #94a3b8; margin-bottom: 2rem;'>Real-Time ML Market Segmentation & Risk Profiling</p>", unsafe_allow_html=True)

    data_payload = fetch_dashboard_data()

    if not data_payload or data_payload.get('status') == 'error':
        err_msg = data_payload.get('message', 'No data or backend offline.') if data_payload else 'Unknown error'
        st.warning(f"Awaiting market data pipeline. Please ensure the FastAPI backend is running.\n\n({err_msg})")
        if st.button("Retry Connection"):
            st.cache_data.clear()
            st.rerun()
        return

    # Unpack Data
    df = pd.DataFrame(data_payload['data'])
    metrics = data_payload['metrics']
    summary = data_payload['summary']
    corr_matrix = data_payload.get('corr_matrix', {})

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">RF Model Validation</div>
            <div class="metric-value">{(metrics.get('accuracy', 0)*100):.0f}% Acc</div>
            <div class="metric-sub">Train-Test Validated (Random Forest) <br/> F1: {metrics.get('f1',0)} | P: {metrics.get('precision',0)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Assets Tracked</div>
            <div class="metric-value">{summary.get('total_coins', 0)}</div>
            <div class="metric-sub">Segmented by dynamic thresholds <br/> Large: >${(summary.get('large_cap_threshold',0)/1e6):.1f}M</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        anomalies_count = len(df[df['is_anomaly'] == True]) if 'is_anomaly' in df.columns else 0
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Anomalies Detected</div>
            <div class="metric-value" style="color: #ef4444;">{anomalies_count}</div>
            <div class="metric-sub">Isolated via Isolation Forest (-1 outliers)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Charts Row 1
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='metric-title' style='margin-bottom:0.25rem;'>Market Cap Distribution (Top 20)</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 1rem;'>Displays the relative market dominance of the top 20 assets.</div>", unsafe_allow_html=True)
        top20 = df.nlargest(20, 'market_cap')
        fig_bar = px.bar(top20, x='symbol', y='market_cap', template="plotly_dark")
        fig_bar.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig_bar.update_traces(marker_color='#3b82f6')
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.markdown("<div class='metric-title' style='margin-bottom:0.25rem;'>Risk Matrix: Liquidity vs Volatility</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 1rem;'>Evaluates risk based on liquidity/volatility. Red indicates ML anomalies.</div>", unsafe_allow_html=True)
        # Handle colors based on anomaly
        df['color'] = df['is_anomaly'].apply(lambda x: 'rgba(239, 68, 68, 0.7)' if x else 'rgba(59, 130, 246, 0.4)')
        df['size'] = df['is_anomaly'].apply(lambda x: 8 if x else 4)
        
        # Adding marginal plots helps understand density even on overlapping areas
        fig_scatter = px.scatter(df, x='norm_liquidity', y='norm_volatility', hover_name='symbol', color='color', size='size', template="plotly_dark", color_discrete_map="identity")
        
        # Use update_traces to improve visibility of overlapping points via border outlines
        fig_scatter.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Component Row: Select Asset
    st.markdown("<hr style='border-color: #2d3748;'>", unsafe_allow_html=True)
    # Ensure options are purely standard Python strings to avoid DataFrame indexing quirks
    symbols_list = [str(x) for x in df['symbol'].head(100).tolist()]
    selected_asset = st.selectbox("Select Asset for Deep Analysis", symbols_list)
    
    # Advanced Candlestick Chart Row
    st.markdown(f"<div class='metric-title' style='margin-bottom:0.25rem;'>Advanced Candlestick Chart (1H) -> {selected_asset}</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 1rem;'>Visualizes Open, High, Low, and Close prices over time for detailed technical analysis.</div>", unsafe_allow_html=True)
    
    candle_err = None
    try:
        candle_data = fetch_candlestick_data_yfinance(selected_asset)
    except Exception as e:
        candle_err = str(e)
        
    if candle_data:
        candle_df = pd.DataFrame(candle_data)
        
        fig_candle = go.Figure(data=[go.Candlestick(
            x=candle_df['timestamp'],
            open=candle_df['open'],
            high=candle_df['high'],
            low=candle_df['low'],
            close=candle_df['close'],
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        )])
        fig_candle.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_rangeslider_visible=False,
            font=dict(color='#d1d4dc')
        )
        st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.info(f"Candlestick data unavailable for {selected_asset} via Yahoo Finance.")
        if candle_err:
            st.error(f"Debug Error: {candle_err}")
        if st.button("Retry Candle Fetch"):
            st.cache_data.clear()
            st.rerun()
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    cr1, cr2 = st.columns(2)
    with cr1:
        st.markdown(f"<div class='metric-title' style='margin-bottom:0.25rem;'>Cumulative Market Cap Growth (%) vs Time -> {selected_asset}</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 1rem;'>Tracks the percentage growth trajectory of the selected asset.</div>", unsafe_allow_html=True)
        hist_payload = fetch_history_data(selected_asset)
        
        if hist_payload and hist_payload['status'] == 'success':
            hist_df = pd.DataFrame(hist_payload['data'])
            fig_area = px.area(hist_df, x='timestamp', y='growth_pct', template="plotly_dark")
            fig_area.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig_area.update_traces(line_color='#10b981', fillcolor='rgba(16,185,129,0.3)')
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.info("Insufficient historical data cache.")

    with cr2:
        st.markdown("<div class='metric-title' style='margin-bottom:0.25rem; text-align: center;'>Cross-Asset Correlation Matrix</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 1rem; text-align: center;'>Shows return correlation. Green: moves together, Red: diverges.</div>", unsafe_allow_html=True)
        if corr_matrix:
            corr_df = pd.DataFrame(corr_matrix)
            fig_heat = px.imshow(corr_df, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn", template="plotly_dark")
            fig_heat.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Correlation data unavailable.")

    # Data Table
    st.markdown("<hr style='border-color: #2d3748;'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-title'>Live Assets Feed Model Data</div>", unsafe_allow_html=True)
    
    display_df = df[['symbol', 'name', 'price', 'percent_change_24h', 'market_segment', 'norm_liquidity', 'norm_volatility', 'risk_score', 'risk_category']].copy()
    display_df.rename(columns={
        "symbol": "Asset", "name": "Name", "price": "Price ($)", "percent_change_24h": "24h Chg (%)",
        "market_segment": "Segment", "norm_liquidity": "Liq Ratio", "norm_volatility": "Vol (Std)", "risk_score": "Risk Score", "risk_category": "Risk Class"
    }, inplace=True)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
