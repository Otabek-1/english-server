from sqlalchemy.orm import Session
from database.session_model import Session as SessionDB
from typing import List, Optional
from datetime import datetime


class SessionService:
    """Session CRUD operations uchun service"""
    
    @staticmethod
    def create_session(db: Session, user_id: int, device_fingerprint: str, 
                       device_name: Optional[str] = None, device_type: Optional[str] = None,
                       browser: Optional[str] = None, ip_address: Optional[str] = None) -> SessionDB:
        """
        Yangi session yaratish
        """
        new_session = SessionDB(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int, active_only: bool = True) -> List[SessionDB]:
        """
        User ning barcha sessiyalarini olish
        """
        query = db.query(SessionDB).filter(SessionDB.user_id == user_id)
        if active_only:
            query = query.filter(SessionDB.is_active == 1)
        return query.all()
    
    @staticmethod
    def get_session_by_fingerprint(db: Session, user_id: int, device_fingerprint: str) -> Optional[SessionDB]:
        """
        Device fingerprint bo'yicha session topish
        """
        return db.query(SessionDB).filter(
            SessionDB.user_id == user_id,
            SessionDB.device_fingerprint == device_fingerprint
        ).first()
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[SessionDB]:
        """
        Session ID bo'yicha session topish
        """
        return db.query(SessionDB).filter(SessionDB.id == session_id).first()
    
    @staticmethod
    def update_session_activity(db: Session, session_id: int) -> bool:
        """
        Session ning last_active vaqtini yangilash
        """
        session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
        if session:
            session.last_active = datetime.utcnow()
            db.commit()
            return True
        return False
    
    @staticmethod
    def deactivate_session(db: Session, session_id: int) -> bool:
        """
        Sessionni deaktivatsiya qilish (logout)
        """
        session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
        if session:
            session.is_active = 0
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        """
        Sessionni o'chirish
        """
        session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_all_user_sessions(db: Session, user_id: int, exclude_session_id: Optional[int] = None) -> int:
        """
        User ning barcha sessiyalarini o'chirish (Optional: bitta sessiyani o'tkalib yuborish)
        """
        query = db.query(SessionDB).filter(SessionDB.user_id == user_id)
        if exclude_session_id:
            query = query.filter(SessionDB.id != exclude_session_id)
        
        count = query.count()
        query.delete()
        db.commit()
        return count
    
    @staticmethod
    def get_session_count(db: Session, user_id: int, active_only: bool = True) -> int:
        """
        User ning sessiya sonini olish
        """
        query = db.query(SessionDB).filter(SessionDB.user_id == user_id)
        if active_only:
            query = query.filter(SessionDB.is_active == 1)
        return query.count()
    
    @staticmethod
    def enforce_max_sessions(db: Session, user_id: int, max_sessions: int = 3) -> Optional[SessionDB]:
        """
        User ning maksimal sessiya limitini tekshirish.
        Agar limitdan ko'p bo'lsa eng eskisini o'chirish.
        
        Returns:
            - Agar o'chirilingan bo'lsa deleted session, aks holda None
        """
        active_sessions = SessionService.get_user_sessions(
            db=db,
            user_id=user_id,
            active_only=True
        )
        
        if len(active_sessions) > max_sessions:
            # Eng eski sessionni topish (eng past created_at)
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            
            # Eng eski sessionni o'chirish
            SessionService.delete_session(db=db, session_id=oldest_session.id)
            return oldest_session
        
        return None
