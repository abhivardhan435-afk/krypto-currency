import asyncio
import httpx
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal, engine, CryptoDataRecord, Base
import pandas as pd
from ml_pipeline import run_ml_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LATEST_ML_RESULTS = {"data": [], "metrics": {}}

async def fetch_crypto_data():
    global LATEST_ML_RESULTS
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "true"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Error fetching from coingecko: {e}")
            return
            
    db = SessionLocal()
    
    # Check if DB is empty
    count = db.query(CryptoDataRecord).count()
    if count == 0:
        logger.info("Database empty, bootstrapping history with sparkline data...")
        records_to_insert = []
        now = datetime.utcnow()
        for coin in data:
            sparkline = coin.get('sparkline_in_7d', {}).get('price', [])
            # Sparkline has up to 168 points (1 per hour for 7 days)
            for i, p in enumerate(sparkline):
                # Subtract hours so the last point is 'now'
                t = now - timedelta(hours=(len(sparkline) - 1 - i))
                records_to_insert.append(
                    CryptoDataRecord(
                        symbol=coin['symbol'],
                        name=coin['name'],
                        price=p,
                        market_cap=coin['market_cap'],  # rough approximation for history
                        volume_24h=coin['total_volume'],
                        percent_change_24h=coin['price_change_percentage_24h'],
                        timestamp=t
                    )
                )
        if records_to_insert:
            db.bulk_save_objects(records_to_insert)
            db.commit()
            logger.info("Bootstrap complete.")

    # Insert current data
    current_records = []
    now = datetime.utcnow()
    for coin in data:
        current_records.append(
            CryptoDataRecord(
                symbol=coin['symbol'],
                name=coin['name'],
                price=coin['current_price'],
                market_cap=coin['market_cap'],
                volume_24h=coin['total_volume'],
                percent_change_24h=coin['price_change_percentage_24h'],
                timestamp=now
            )
        )
    db.bulk_save_objects(current_records)
    db.commit()
    
    # ------------------ Process Data for ML Pipeline ------------------
    # Query history from DB to calculate rolling volatility
    # We'll take the latest 100 points for each coin
    
    # We can use pandas to read from sql
    try:
        # Get last 7 days basically
        cutoff = now - timedelta(days=7)
        df_history = pd.read_sql(
            db.query(CryptoDataRecord).filter(CryptoDataRecord.timestamp >= cutoff).statement, 
            db.bind
        )
        
        # Sort values
        df_history = df_history.sort_values(by=['symbol', 'timestamp'])
        
        # Calculate Returns & Volatility
        df_history['returns'] = df_history.groupby('symbol')['price'].pct_change()
        volatility_df = df_history.groupby('symbol')['returns'].std().reset_index()
        volatility_df.rename(columns={'returns': 'volatility'}, inplace=True)
        
        # Get the latest row for each symbol for the current market state
        latest_df = df_history.drop_duplicates(subset=['symbol'], keep='last').copy()
        
        # Merge volatility
        latest_df = pd.merge(latest_df, volatility_df, on='symbol', how='left')
        latest_df['volatility'] = latest_df['volatility'].fillna(0)
        
        # Run ML Pipeline
        ml_df, metrics = run_ml_pipeline(latest_df)
        
        ml_df = ml_df.replace({pd.NA: None, float("nan"): None})
        
        LATEST_ML_RESULTS["data"] = ml_df.to_dict(orient="records")
        LATEST_ML_RESULTS["metrics"] = metrics
        logger.info("ML Pipeline updated successfully.")
        
    except Exception as e:
        logger.error(f"Error in ML pipeline processing: {e}")
        
    finally:
        db.close()


async def background_task():
    while True:
        await fetch_crypto_data()
        await asyncio.sleep(60)

def init_db():
    Base.metadata.create_all(bind=engine)
