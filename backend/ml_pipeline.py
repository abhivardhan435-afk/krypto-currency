import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from models import CryptoRecord

def get_market_intelligence(db: Session):
    # Fetch all records to construct a time-series if available
    query = db.query(CryptoRecord).order_by(CryptoRecord.timestamp.asc())
    df = pd.read_sql(query.statement, db.get_bind())
    
    if df.empty:
        return {"status": "error", "message": "No data available"}
    
    # We want latest records for current view
    latest_timestamp = df['timestamp'].max()
    latest_df = df[df['timestamp'] == latest_timestamp].copy()
    
    # Drop where market_cap is 0 to avoid division by zero
    latest_df = latest_df[latest_df['market_cap'] > 0].copy()
    if latest_df.empty:
        return {"status": "error", "message": "Insufficient active data"}
    
    # 1. Compute Liquidity Ratio
    latest_df['liquidity_ratio'] = latest_df['volume_24h'] / latest_df['market_cap']
    
    # 2. Compute Volatility (Rolling Std Dev of Price Returns)
    # We will compute price returns for each symbol across time
    # Shift prices by symbol to get returns
    df['price_return'] = df.groupby('symbol')['price'].pct_change()
    
    # Compute std dev per symbol
    volatility_df = df.groupby('symbol')['price_return'].std().reset_index()
    volatility_df.rename(columns={'price_return': 'volatility'}, inplace=True)
    
    # Fill NaN volatility (if only 1 data point) with 0 or mean
    volatility_df['volatility'] = volatility_df['volatility'].fillna(0)
    
    # Merge latest with volatility
    latest_df = latest_df.merge(volatility_df, on='symbol', how='left')
    latest_df['volatility'] = latest_df['volatility'].fillna(0)
    
    # 3. Normalize Liquidity and Volatility
    scaler = MinMaxScaler()
    latest_df[['norm_liquidity', 'norm_volatility']] = scaler.fit_transform(latest_df[['liquidity_ratio', 'volatility']])
    
    # 4. Composite Risk Score
    # Assuming less liquidity = more risk. Volatility directly proportional to risk.
    latest_df['liquidity_risk'] = 1 - latest_df['norm_liquidity']
    latest_df['volatility_risk'] = latest_df['norm_volatility']
    # If volatility is 0 because of lack of data, we might proxy with abs(price_change) or just stick to 0.
    latest_df['risk_score'] = 0.5 * latest_df['liquidity_risk'] + 0.5 * latest_df['volatility_risk']
    
    # 5. Dynamic Market Segmentation
    # Top 30% Large, Middle 40% Mid, Bottom 30% Small
    cap_30 = latest_df['market_cap'].quantile(0.30)
    cap_70 = latest_df['market_cap'].quantile(0.70)
    
    def classify_cap(x):
        if x <= cap_30: return "Small-Cap"
        elif x <= cap_70: return "Mid-Cap"
        else: return "Large-Cap"
        
    latest_df['market_segment'] = latest_df['market_cap'].apply(classify_cap)
    
    # 6. ML Integration
    features = latest_df[['norm_liquidity', 'norm_volatility', 'percent_change_24h']].fillna(0)
    
    # K-Means
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    latest_df['cluster'] = kmeans.fit_predict(features)
    
    # Isolation Forest
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    # Returns 1 for normal, -1 for anomaly
    latest_df['is_anomaly'] = iso_forest.fit_predict(features) == -1
    
    # Random Forest for Risk Category prediction
    # First, label data into Risk Category based on Risk Score percentiles
    risk_33 = latest_df['risk_score'].quantile(0.333)
    risk_66 = latest_df['risk_score'].quantile(0.666)
    
    def classify_risk(x):
        if x <= risk_33: return "Low"
        elif x <= risk_66: return "Medium"
        else: return "High"
        
    latest_df['risk_category'] = latest_df['risk_score'].apply(classify_risk)
    
    # Train test split for RF evaluation
    X = latest_df[['norm_liquidity', 'norm_volatility', 'percent_change_24h', 'market_cap']]
    y = latest_df['risk_category']
    
    # Need > 1 class in y to do split properly
    metrics = {"accuracy": 0, "precision": 0, "recall": 0, "f1": 0}
    if len(y.unique()) > 1 and len(latest_df) > 10:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        y_pred = rf.predict(X_test)
        metrics = {
            "accuracy": np.round(accuracy_score(y_test, y_pred), 2),
            "precision": np.round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 2),
            "recall": np.round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 2),
            "f1": np.round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 2)
        }
    
    # 7. Correlation Matrix for top 15 symbols
    top_15_symbols = latest_df.nlargest(15, 'market_cap')['symbol'].tolist()
    top_15_df = df[df['symbol'].isin(top_15_symbols)]
    pivot_df = top_15_df.pivot_table(index='timestamp', columns='symbol', values='price')
    
    if len(pivot_df) > 1:
        corr_df = pivot_df.pct_change().corr().fillna(0).round(2)
    else:
        corr_df = pd.DataFrame(1.0, index=top_15_symbols, columns=top_15_symbols)
        
    corr_matrix = corr_df.to_dict()
    
    # Format the payload for the frontend
    # Replace NaN with None for JSON serialization
    latest_df = latest_df.replace({np.nan: None})
    
    data = latest_df.to_dict(orient="records")
    
    return {
        "status": "success",
        "timestamp": latest_timestamp.isoformat(),
        "metrics": metrics,
        "data": data,
        "corr_matrix": corr_matrix,
        "summary": {
            "total_coins": len(data),
            "large_cap_threshold": cap_70,
            "small_cap_threshold": cap_30
        }
    }
