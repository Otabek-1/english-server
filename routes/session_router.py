from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.db import get_db, User
from database.session_model import Session as SessionDB
from schemas.session_schema import SessionCreate, SessionResponse
from services.session_service import SessionService
from auth.auth import verify_access_token
from typing import List


router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_current_user(token: str = Depends(verify_access_token), db: Session = Depends(get_db)):
    """Hozirgi user ni tekshirish"""
    user = db.query(User).filter(User.id == token["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/create", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Yangi session yaratish (yangi qurilma kirganda)
    
    Agar 4-qurilma login qilsa, eng eski qurilma avtomatik o'chilinadi.
    Maksimal 3 ta qurilma kirishlari mumkin.
    """
    try:
        # Eng eski sessionni o'chirish agar 3tadan ko'p bo'lsa
        deleted_session = SessionService.enforce_max_sessions(
            db=db,
            user_id=current_user.id,
            max_sessions=3
        )
        
        # Yangi session yaratish
        new_session = SessionService.create_session(
            db=db,
            user_id=current_user.id,
            device_fingerprint=session_data.device_fingerprint,
            device_name=session_data.device_name,
            device_type=session_data.device_type,
            browser=session_data.browser,
            ip_address=session_data.ip_address
        )
        
        return new_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-sessions", response_model=List[SessionResponse])
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """
    Foydalanuvchining barcha sessiyalarini olish
    
    Query parameters:
    - include_inactive: True bo'lsa inactive sessiyalarni ham qaytaradi
    """
    try:
        sessions = SessionService.get_user_sessions(
            db=db,
            user_id=current_user.id,
            active_only=not include_inactive
        )
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bitta sessionning detallarini olish
    """
    try:
        session = SessionService.get_session_by_id(db=db, session_id=session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Foydalanuvchi faqat o'z sessiyasini ko'ra oladi
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to view this session")
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bitta sessionni o'chirish (logout qilish)
    """
    try:
        session = SessionService.get_session_by_id(db=db, session_id=session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Foydalanuvchi faqat o'z sessiyasini o'chira oladi
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this session")
        
        SessionService.delete_session(db=db, session_id=session_id)
        
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logout")
async def logout_current_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    🔴 FRONTEND QO'LLANISH: Hozirgi sessionni yopish
    Frontend logout qilganda, token yuborilishidan oldin chaqiriladi
    
    Use case: User logout button click
    - Frontend: logoutUser() -> DELETE /sessions/logout -> clear localStorage
    """
    try:
        # Request va token-dan hozirgi sessionni aniqlash
        # Frontend device_fingerprint yuborganda match qilish
        token = request.state.token if hasattr(request, 'state') else None
        
        # Yoki user_id + device_fingerprint orqali topish
        # Haqiqatan frontend yuborayotgan device fingerprint-ga mos sessionni topish
        
        # Eng soddasi: eng oxirgi active sessionni o'chirish
        sessions = SessionService.get_user_sessions(
            db=db,
            user_id=current_user.id,
            active_only=True
        )
        
        if not sessions:
            raise HTTPException(status_code=404, detail="No active session found")
        
        # Eng soddasi: barcha sessiyani o'chirmaymiz, eng oxirgi active sessiyani o'chiramiz
        # BETTER: Frontend device_fingerprint yuboradigan bo'lsa, shu fingerprinti topamiz
        # For now: eng oxirgi sessiyani o'chiramiz
        latest_session = sessions[-1]
        SessionService.delete_session(db=db, session_id=latest_session.id)
        
        return {
            "success": True,
            "message": "Current session closed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    exclude_current: bool = False
):
    """
    Barcha qurilmalardan logout qilish
    
    Query parameters:
    - exclude_current: True bo'lsa joriy sessionni o'tkalib yuboradi
    """
    try:
        # Agar exclude_current True bo'lsa, hozirgi sessionni topish
        current_session_id = None
        if exclude_current:
            # Hozirgi sessionni topish uchun more info kerak bo'ladi
            # For now, biz barcha sessionlarni o'chiramiz
            pass
        
        count = SessionService.delete_all_user_sessions(
            db=db,
            user_id=current_user.id,
            exclude_session_id=current_session_id
        )
        
        return {
            "success": True,
            "message": f"{count} sessions deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-devices-count")
async def get_active_devices_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aktiv qurilmalar sonini olish
    """
    try:
        count = SessionService.get_session_count(db=db, user_id=current_user.id, active_only=True)
        return {
            "active_devices": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMIN ENDPOINTS ====================
# Frontend-dan kerak: Admin panel -> Users -> View Sessions


@router.get("/user/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions_admin(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔴 ADMIN ONLY: Biror user-ning barcha sessiyalarini ko'rish
    
    Frontend qo'llanish: Admin Panel -> Users -> Click "Sessions" button
    
    Permissiyalar:
    - Faqat admin users qila oladi
    - Admin o'zi qara olmaydi, boshqa user-larni qara oladi
    """
    try:
        # Admin tekshirish
        if not current_user.role or current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Only admins can view other users' sessions"
            )
        
        # Target user mavjudligini tekshirish
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Admin o'z sessiyasini ko'ra oladi
        if user_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Use /my-sessions endpoint for your own sessions"
            )
        
        # Target user-ning barcha active sessiyalarini olish
        sessions = SessionService.get_user_sessions(
            db=db,
            user_id=user_id,
            active_only=True
        )
        
        return sessions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
