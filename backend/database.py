from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./crypto_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class CryptoDataRecord(Base):
    __tablename__ = "crypto_data_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    price = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    percent_change_24h = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
