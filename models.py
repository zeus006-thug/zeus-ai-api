# models.py

from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.sql import func
from .database import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_request_date = Column(Date, nullable=True)
    request_count_today = Column(Integer, default=0)
