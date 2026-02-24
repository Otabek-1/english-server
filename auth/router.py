from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from .auth import hash_password, create_access_token, create_refresh_token, verify_password, verify_access_token, verify_refresh_token
from .schema import (
    RegisterUser,
    LoginUser,
    TokenRefreshSchema,
    ForgotPasswordRequest,
    VerifyResetCodeRequest,
    ResetPasswordRequest,
)
from database.db import get_db, User, Notification, PasswordResetCode
from database.session_model import Session as SessionDB
from services.session_service import SessionService
from services.email_service import send_password_reset_code_email
from datetime import datetime, timedelta
from fastapi import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os
import re
import random
import secrets
import hashlib
from user_agents import parse as parse_user_agent


router = APIRouter(prefix="/auth")

oauth = OAuth()

RAMADAN_PREMIUM_UNTIL = datetime(datetime.utcnow().year, 5, 1, 23, 59, 59)
PASSWORD_RESET_CODE_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_CODE_EXPIRE_MINUTES", "15"))
PASSWORD_RESET_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_MAX_ATTEMPTS", "5"))

# ===== HELPER FUNCTIONS =====
def get_client_ip(request: Request) -> str:
    """Client IP address olish (proxy behind'da ham ishlaydi)"""
    if request.headers.get('x-forwarded-for'):
        return request.headers.get('x-forwarded-for').split(',')[0].strip()
    return request.client.host if request.client else "0.0.0.0"

def generate_device_fingerprint(ip: str, user_agent: str) -> str:
    """IP + User-Agent dan unique fingerprint generatsiya qilish"""
    fingerprint_string = f"{ip}:{user_agent}"
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def parse_device_info(user_agent_string: str):
    """User-Agent'dan device ma'lumotlarini chiqarish"""
    try:
        ua = parse_user_agent(user_agent_string)
        
        # Device type aniqlash
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        else:
            device_type = "desktop"
        
        # Device name
        device_name = str(ua.device.family) if ua.device.family else "Unknown"
        
        # Browser
        browser = str(ua.browser.family) if ua.browser.family else "Unknown"
        
        return {
            "device_type": device_type,
            "device_name": device_name,
            "browser": browser
        }
    except:
        return {
            "device_type": "unknown",
            "device_name": "Unknown",
            "browser": "Unknown"
        }

def create_session_for_user(db: Session, user_id: int, request: Request) -> SessionDB:
    """Auto-create session when user logs in"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get('user-agent', '')
    
    # Device fingerprint generatsiya qilish
    device_fingerprint = generate_device_fingerprint(ip_address, user_agent)
    
    # Device info parse qilish
    device_info = parse_device_info(user_agent)
    
    # Agar 3tadan ko'p session bo'lsa eng eskisini o'chirish
    SessionService.enforce_max_sessions(db=db, user_id=user_id, max_sessions=3)
    
    # Yangi session yaratish
    session = SessionService.create_session(
        db=db,
        user_id=user_id,
        device_fingerprint=device_fingerprint,
        device_name=device_info["device_name"],
        device_type=device_info["device_type"],
        browser=device_info["browser"],
        ip_address=ip_address
    )
    
    return session


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _build_password_reset_code_hash(email: str, code: str) -> str:
    secret = os.getenv("SECRET_KEY", "mockstream-secret")
    raw = f"{_normalize_email(email)}:{code}:{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_password_reset_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def generate_unique_username(name: str, db: Session) -> str:
    """
    Google ismidan clean username generatsiya qilish
    - Spaces va special characters olib tashlash
    - Random 2-3 talik suffix qo'shish
    """
    # Spaces va special characters olib tashlash (faqat alphanumeric saqla)
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    
    # Agar name bo'sh bo'lsa, default username
    if not clean_name:
        clean_name = "user"
    
    # Random suffix qo'shish (10-999 oralig'ida)
    while True:
        suffix = random.randint(10, 999)
        username = f"{clean_name}{suffix}"
        
        # Username unique ekanligini tekshirish
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            return username

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    email = user_info["email"]
    name = user_info["name"]
    avatar = user_info["picture"]

    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Clean username generatsiya qilish
        username = generate_unique_username(name, db)
        
        user = User(
            username=username,
            email=email,
            password=None,
            google_avatar=avatar,
            premium_duration=RAMADAN_PREMIUM_UNTIL
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Session yaratish
    session = create_session_for_user(db=db, user_id=user.id, request=request)
    
    payload = {"id": user.id, "email": user.email}

    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return RedirectResponse(
        f"{os.getenv('FRONTEND_URL')}/auth?access={access}&refresh={refresh}&session_id={session.id}"
    )

@router.post("/register")
def register_user(data: RegisterUser, request: Request, db: Session = Depends(get_db)):
    email_exists = db.query(User).filter(User.email == data.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    try:
        new_user = User(
            username=data.username,
            email=data.email,
            password=hash_password(data.password),
            premium_duration=RAMADAN_PREMIUM_UNTIL
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Session yaratish
        session = create_session_for_user(db=db, user_id=new_user.id, request=request)
        
        access_token = create_access_token({"id":new_user.id,"email":new_user.email})
        refresh_token = create_refresh_token({"id":new_user.id,"email":new_user.email})
        welcome_notification = Notification(title=f"Xush kelibsiz, {new_user.username}! 👋",body=f"Bizning platformamizga qo'shilganingiz uchun tashakkur. Ingliz tili o'rganishni boshlang va o'z darajangizni oshiring!", user_id=new_user.id)
        db.add(welcome_notification)
        db.commit()
        db.refresh(welcome_notification)
        return {
            "message":"User registered",
            "access_token":access_token,
            "refresh_token":refresh_token,
            "token_type": "Bearer",
            "session_id": session.id,
            "device_type": session.device_type
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error in register_user: {Exception}")

@router.post("/login")
def login_user(data:LoginUser, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password incorrect.")
    
    # Session yaratish
    session = create_session_for_user(db=db, user_id=user.id, request=request)
    
    payload ={"id":user.id,"email":user.email}
    
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "session_id": session.id,
        "device_type": session.device_type
    }

@router.post("/verify")
def refresh_token(data:TokenRefreshSchema):
    payload = verify_refresh_token(data.refresh_token)
    
    if payload is None:
        raise HTTPException(401, "Invalid refresh token")

    new_access = create_access_token({"id": payload["id"], "email": payload["email"]})

    return {"access_token": new_access, "token_type": "Bearer"}


@router.post("/forgot-password/request")
def request_forgot_password_code(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic_message = "If an account exists for this email, a verification code has been sent."
    email = _normalize_email(data.email)
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        return {"message": generic_message}

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=PASSWORD_RESET_CODE_EXPIRE_MINUTES)
    code = _generate_password_reset_code()
    code_hash = _build_password_reset_code_hash(email=email, code=code)

    try:
        db.query(PasswordResetCode).filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
        ).update({PasswordResetCode.used_at: now}, synchronize_session=False)

        db.add(
            PasswordResetCode(
                user_id=user.id,
                code_hash=code_hash,
                expires_at=expires_at,
                attempts=0,
            )
        )

        email_sent, detail = send_password_reset_code_email(
            to_email=user.email,
            username=user.username or "User",
            code=code,
            expires_minutes=PASSWORD_RESET_CODE_EXPIRE_MINUTES,
        )
        if not email_sent:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not send reset code email. {detail}",
            )

        db.commit()
        return {"message": generic_message}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in forgot password request.",
        )


@router.post("/forgot-password/verify")
def verify_forgot_password_code(data: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    email = _normalize_email(data.email)
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code or email.")

    now = datetime.utcnow()
    reset_row = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
        )
        .order_by(PasswordResetCode.id.desc())
        .first()
    )

    if not reset_row or reset_row.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired. Request a new code.")

    if reset_row.attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
        reset_row.used_at = now
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Request a new code.",
        )

    submitted_hash = _build_password_reset_code_hash(email=email, code=data.code.strip())
    if submitted_hash != reset_row.code_hash:
        reset_row.attempts += 1
        if reset_row.attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
            reset_row.used_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")

    return {"message": "Code verified."}


@router.post("/forgot-password/reset")
def reset_forgot_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = _normalize_email(data.email)
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code or email.")

    now = datetime.utcnow()
    reset_row = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.user_id == user.id,
            PasswordResetCode.used_at.is_(None),
        )
        .order_by(PasswordResetCode.id.desc())
        .first()
    )

    if not reset_row or reset_row.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired. Request a new code.")

    if reset_row.attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
        reset_row.used_at = now
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Request a new code.",
        )

    submitted_hash = _build_password_reset_code_hash(email=email, code=data.code.strip())
    if submitted_hash != reset_row.code_hash:
        reset_row.attempts += 1
        if reset_row.attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
            reset_row.used_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")

    try:
        user.password = hash_password(data.new_password)
        reset_row.used_at = now
        db.commit()
        return {"message": "Password updated successfully."}
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in resetting password.",
        )
