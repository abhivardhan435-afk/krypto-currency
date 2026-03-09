from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class CryptoRecord(Base):
    __tablename__ = "crypto_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    percent_change_24h = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
