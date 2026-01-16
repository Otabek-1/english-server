from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    """Session yaratish uchun schema"""
    device_fingerprint: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None


class SessionResponse(BaseModel):
    """Session ma'lumotlarini qaytarish uchun schema"""
    id: int
    user_id: int
    device_fingerprint: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_active: datetime
    is_active: int
    
    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    """Session o'zgartirish uchun schema"""
    last_active: Optional[datetime] = None
    is_active: Optional[int] = None
