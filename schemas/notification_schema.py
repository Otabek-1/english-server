from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    body: str

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    is_read: bool | None = None

class NotificationOut(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
