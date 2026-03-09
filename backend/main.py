from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

from database import engine, Base, get_db
from fetcher import fetch_crypto_data
from ml_pipeline import get_market_intelligence
import time
import os

app = FastAPI(title="Crypto Market Intelligence API")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()

def scheduled_job():
    db = next(get_db())
    fetch_crypto_data(db)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    
    # fetch initial data immediately
    # scheduled_job()
    
    # Schedule to fetch data every 60 seconds
    scheduler.add_job(scheduled_job, 'interval', seconds=60)
    scheduler.start()
    
    # Do initial fetch here to ensure we have data immediately
    # run in background
    db = next(get_db())
    fetch_crypto_data(db)

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/api/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    result = get_market_intelligence(db)
    return result

@app.post("/api/fetch")
def trigger_fetch(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(fetch_crypto_data, db)
    return {"message": "Data fetch started in background."}

from models import CryptoRecord

@app.get("/api/history/{symbol}")
def get_coin_history(symbol: str, db: Session = Depends(get_db)):
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
