import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def compute_metrics(prices_series):
    if len(prices_series) < 2:
        return 0.0
    returns = prices_series.pct_change().dropna()
    if len(returns) == 0:
        return 0.0
    return returns.std()

def run_ml_pipeline(df: pd.DataFrame):
    """
    df: Dataframe with at least:
    symbol, market_cap, volume_24h, volatility
    """
    if len(df) < 10:
        # Not enough data for meaningful ML
        return df, {}
        
    df = df.copy()
    
    # 1. Dynamic Market Segmentation
    # Large-Cap (Top 30%), Mid-Cap (Middle 40%), Small-Cap (Bottom 30%)
    p70 = df['market_cap'].quantile(0.70)
    p30 = df['market_cap'].quantile(0.30)
    
    def get_cap_category(mcap):
        if mcap >= p70: return 'Large-Cap'
        elif mcap >= p30: return 'Mid-Cap'
        else: return 'Small-Cap'
        
    df['cap_category'] = df['market_cap'].apply(get_cap_category)
    
    # 2. Liquidity and Volatility Modeling
    df['liquidity_ratio'] = df['volume_24h'] / df['market_cap']
    
    # Normalize Liquidity and Volatility
    scaler = StandardScaler()
    # Handle cases where volatility might be all 0s
    if df['volatility'].std() == 0:
        df['vol_norm'] = 0.0
    else:
        df['vol_norm'] = scaler.fit_transform(df[['volatility']])
        
    if df['liquidity_ratio'].std() == 0:
        df['liq_norm'] = 0.0
    else:
        df['liq_norm'] = scaler.fit_transform(df[['liquidity_ratio']])
        
    # Liquidity risk is inverse to liquidity (low liquidity = high risk)
    # But for a risk score, we can standardise. Let's invert liquidity norm so high liq norm = low risk.
    df['liq_risk'] = -df['liq_norm']
    
    # Composite Risk Score: Weighted(Liquidity Risk + Volatility Risk)
    # Give equal weights
    df['risk_score'] = 0.5 * df['liq_risk'] + 0.5 * df['vol_norm']
    
    # Rule-based Risk Category
    # Bottom 33% low, Mid 33% medium, Top 33% high
    try:
        df['risk_category'] = pd.qcut(df['risk_score'], 3, labels=['Low', 'Medium', 'High'])
    except ValueError:
        df['risk_category'] = 'Medium'
        
    # 3. ML Integration
    # K-Means clustering (using liquidity and volatility)
    features = df[['liquidity_ratio', 'volatility']].fillna(0)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(features)
    
    # Isolation Forest to detect anomalous cryptocurrencies
    iso = IsolationForest(contamination=0.1, random_state=42)
    df['anomaly'] = iso.fit_predict(features) # -1 is anomaly, 1 is normal
    df['is_anomaly'] = df['anomaly'] == -1
    
    # Random Forest to predict risk category (Low, Medium, High)
    metrics_result = {}
    if len(df['risk_category'].unique()) > 1:
        X = df[['liquidity_ratio', 'volatility', 'market_cap', 'volume_24h']]
        y = df['risk_category']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        rf = RandomForestClassifier(n_estimators=50, random_state=42)
        rf.fit(X_train, y_train)
        
        y_pred = rf.predict(X_test)
        
        metrics_result = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            # Use macro or weighted average for multi-class
            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
        }
        
        # Predict on all data to compare rule-based vs ML
        df['ml_risk_category'] = rf.predict(X)
        
        # Output explanation
        def explain_risk(row):
            if row['is_anomaly']:
                return "Flagged as anomalous due to unusual combination of liquidity and volatility."
            elif row['ml_risk_category'] == 'High':
                return "High volatility and/or low liquidity indicated by RF model."
            elif row['ml_risk_category'] == 'Low':
                return "Stable asset with good liquidity and low volatility."
            else:
                return "Moderate risk based on typical market behavior."
        df['risk_explanation'] = df.apply(explain_risk, axis=1)
    else:
        df['ml_risk_category'] = df['risk_category']
        df['risk_explanation'] = "Insufficient variance for ML explanation."
        
    # Replace NaN with None for JSON serialization
    df = df.replace({pd.NA: None, np.nan: None})
    
    return df, metrics_result
