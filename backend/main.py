from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, CryptoDataRecord, engine, Base
import asyncio
from fetcher import fetch_crypto_data, LATEST_ML_RESULTS, background_task, logger
import pandas as pd

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Crypto Market Intelligence API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting background fetcher task...")
    asyncio.create_task(background_task())

import numpy as np
from fastapi.encoders import jsonable_encoder

@app.get("/api/crypto/latest")
async def get_latest_data():
    try:
        # Prevent completely invalid JSON by ensuring basic types
        data_clean = []
        for row in LATEST_ML_RESULTS.get("data", []):
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v):
                    clean_row[k] = None
                else:
                    clean_row[k] = v
            data_clean.append(clean_row)
        
        return JSONResponse(content=jsonable_encoder({
            "data": data_clean,
            "metrics": LATEST_ML_RESULTS.get("metrics", {})
        }))
    except Exception as e:
        logger.error(f"Error in /api/crypto/latest: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/crypto/history")
async def get_dataset_csv():
    """
    Download dataset as CSV.
    We just export the SQLite DB history.
    """
    db = SessionLocal()
    try:
        df = pd.read_sql(db.query(CryptoDataRecord).statement, db.bind)
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=crypto_history.csv"})
    finally:
        db.close()

@app.get("/api/crypto/history/{symbol}")
async def get_coin_history(symbol: str):
    """
    Get time-series history for a specific coin.
    """
    db = SessionLocal()
    try:
        # Fetch the last 7 days of data for the coin, ordered by timestamp
        query = db.query(
            CryptoDataRecord.timestamp,
            CryptoDataRecord.market_cap
        ).filter(
            CryptoDataRecord.symbol == symbol.lower()
        ).order_by(
            CryptoDataRecord.timestamp.asc()
        )
        
        df = pd.read_sql(query.statement, db.bind)
        
        # Convert timestamp to string if necessary, handle NaNs
        df = df.replace({pd.NA: None, float("nan"): None})
        
        history_data = []
        for index, row in df.iterrows():
            history_data.append({
                "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else row["timestamp"],
                "market_cap": row["market_cap"]
            })
            
        return JSONResponse(content={"symbol": symbol, "history": history_data})
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        db.close()
