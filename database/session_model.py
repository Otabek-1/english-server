from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_fingerprint = Column(String(255), nullable=False)  # Device unique identifier
    device_name = Column(String(100), nullable=True)  # e.g., "iPhone 12", "Samsung Galaxy S21"
    device_type = Column(String(50), nullable=True)  # e.g., "mobile", "desktop", "tablet"
    browser = Column(String(50), nullable=True)  # e.g., "Chrome", "Safari"
    ip_address = Column(String(50), nullable=True)  # User IP address
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive (logout qilingan)
    
    # Relationship to User
    user = relationship("User", backref="sessions")
