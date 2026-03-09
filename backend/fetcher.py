import requests
from sqlalchemy.orm import Session
from models import CryptoRecord
from datetime import datetime

def fetch_crypto_data(db: Session):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        timestamp = datetime.utcnow()
        
        for item in data:
            record = CryptoRecord(
                symbol=item.get("symbol", "").upper(),
                name=item.get("name", ""),
                price=item.get("current_price", 0.0) or 0.0,
                market_cap=item.get("market_cap", 0.0) or 0.0,
                volume_24h=item.get("total_volume", 0.0) or 0.0,
                percent_change_24h=item.get("price_change_percentage_24h", 0.0) or 0.0,
                timestamp=timestamp
            )
            db.add(record)
        
        db.commit()
        print(f"[{timestamp}] Successfully fetched and saved {len(data)} records.")
    except Exception as e:
        print(f"Error fetching data: {e}")
        db.rollback()
