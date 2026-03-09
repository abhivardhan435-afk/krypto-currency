import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import engine, Base, get_db
from ml_pipeline import get_market_intelligence
from models import CryptoRecord
from fetcher import fetch_crypto_data
from apscheduler.schedulers.background import BackgroundScheduler

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

# --- BACKEND INTEGRATION ---
@st.cache_resource
def init_background_jobs():
    Base.metadata.create_all(bind=engine)
    scheduler = BackgroundScheduler()
    
    def scheduled_job():
        db = next(get_db())
        fetch_crypto_data(db)
        
    scheduler.add_job(scheduled_job, 'interval', seconds=60)
    scheduler.start()
    
    # Do initial fetch here to ensure we have data immediately
    db = next(get_db())
    fetch_crypto_data(db)
    
    return scheduler

# Start the background scheduler
_ = init_background_jobs()

@st.cache_data(ttl=60)
def fetch_dashboard_data():
    try:
        db = next(get_db())
        return get_market_intelligence(db)
    except Exception as e:
        st.error(f"Cannot process data: {e}")
    return None

@st.cache_data(ttl=60)
def fetch_history_data(symbol):
    try:
        db = next(get_db())
        records = db.query(CryptoRecord).filter(
            CryptoRecord.symbol == symbol.upper()
        ).order_by(CryptoRecord.timestamp.asc()).all()
        
        if not records:
            return {"status": "error", "message": "No data found for symbol"}
            
        history = []
        initial_price = records[0].price if records[0].price > 0 else 1
        
        for r in records:
            growth_pct = ((r.price - initial_price) / initial_price) * 100
            history.append({
                "timestamp": r.timestamp.isoformat(),
                "price": r.price,
                "growth_pct": growth_pct
            })
            
        return {"status": "success", "symbol": symbol.upper(), "data": history}
    except Exception as e:
        return None

# --- MAIN RENDER ---
def main():
    st.markdown(
        "<h1 style='background: linear-gradient(90deg, #60a5fa, #3b82f6, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>KRYPTOS Intelligence</h1>", 
        unsafe_allow_html=True
    )
    st.markdown("<p style='color: #94a3b8; margin-bottom: 2rem;'>Real-Time ML Market Segmentation & Risk Profiling</p>", unsafe_allow_html=True)

    data_payload = fetch_dashboard_data()

    if not data_payload or data_payload.get('status') == 'error':
        st.warning("Awaiting market data pipeline. Please ensure the FastAPI backend is running.")
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
        st.markdown("<div class='metric-title'>Market Cap Distribution (Top 20)</div>", unsafe_allow_html=True)
        top20 = df.nlargest(20, 'market_cap')
        fig_bar = px.bar(top20, x='symbol', y='market_cap', template="plotly_dark")
        fig_bar.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        fig_bar.update_traces(marker_color='#3b82f6')
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.markdown("<div class='metric-title'>Risk Matrix: Liquidity vs Volatility</div>", unsafe_allow_html=True)
        # Handle colors based on anomaly
        df['color'] = df['is_anomaly'].apply(lambda x: '#ef4444' if x else '#3b82f6')
        df['size'] = df['is_anomaly'].apply(lambda x: 12 if x else 6)
        
        fig_scatter = px.scatter(df, x='norm_liquidity', y='norm_volatility', hover_name='symbol', color='color', size='size', template="plotly_dark", color_discrete_map="identity")
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Component Row: Select Asset
    st.markdown("<hr style='border-color: #2d3748;'>", unsafe_allow_html=True)
    selected_asset = st.selectbox("Select Asset for Deep Analysis", df['symbol'].head(100).tolist())
    
    cr1, cr2 = st.columns(2)
    with cr1:
        st.markdown(f"<div class='metric-title'>Cumulative Market Cap Growth (%) vs Time -> {selected_asset}</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='metric-title'>Cross-Asset Correlation Matrix</div>", unsafe_allow_html=True)
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
