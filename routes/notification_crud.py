from sqlalchemy.orm import Session
from database.db import Notification
from schemas.notification_schema import NotificationCreate, NotificationUpdate

def create_notification(db: Session, data: NotificationCreate):
    new_notif = Notification(**data.dict())
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    return new_notif


def get_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()


def get_notification_by_id(db: Session, notif_id: int):
    return db.query(Notification).filter(Notification.id == notif_id).first()


def update_notification(db: Session, notif_id: int, data: NotificationUpdate):
    notif = get_notification_by_id(db, notif_id)
    if not notif:
        return None
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(notif, key, value)

    db.commit()
    db.refresh(notif)
    return notif


def delete_notification(db: Session, notif_id: int):
    notif = get_notification_by_id(db, notif_id)
    if not notif:
        return None

    db.delete(notif)
    db.commit()
    return True
