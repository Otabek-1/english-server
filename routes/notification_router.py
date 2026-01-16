from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db, User
from auth.auth import get_current_user
from .notification_crud import (
    create_notification, get_notifications, get_notification_by_id,
    update_notification, delete_notification
)
from schemas.notification_schema import NotificationCreate, NotificationUpdate, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationOut)
def create(data: NotificationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_notification(db, data)


@router.get("/{user_id}", response_model=list[NotificationOut])
def get_all(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own notifications")
    return get_notifications(db, user_id)


@router.get("/detail/{notif_id}", response_model=NotificationOut)
def get_one(notif_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = get_notification_by_id(db, notif_id)
    if not notif:
        raise HTTPException(404, "Notification not found")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own notifications")
    return notif


@router.put("/{notif_id}", response_model=NotificationOut)
def update(notif_id: int, data: NotificationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = get_notification_by_id(db, notif_id)
    if not notif:
        raise HTTPException(404, "Notification not found")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own notifications")
    notif = update_notification(db, notif_id, data)
    return notif


@router.delete("/{notif_id}")
def delete(notif_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = get_notification_by_id(db, notif_id)
    if not notif:
        raise HTTPException(404, "Notification not found")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own notifications")
    success = delete_notification(db, notif_id)
    if not success:
        raise HTTPException(404, "Notification not found")
    return {"message": "Notification deleted"}
