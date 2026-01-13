from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .auth import hash_password, create_access_token, create_refresh_token, verify_password, verify_access_token, verify_refresh_token
from .schema import RegisterUser, LoginUser, TokenRefreshSchema
from database.db import get_db, User, Notification
from datetime import datetime, timedelta
from fastapi import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os
import re
import random


router = APIRouter(prefix="/auth")

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
            google_avatar=avatar
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    payload = {"id": user.id, "email": user.email}

    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return RedirectResponse(
        f"{os.getenv('FRONTEND_URL')}/auth?access={access}&refresh={refresh}"
    )

@router.post("/register")
def register_user(data: RegisterUser, db: Session = Depends(get_db)):
    email_exists = db.query(User).filter(User.email == data.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    try:
        now = datetime.utcnow() + timedelta(days=5)
        new_user = User(username=data.username, email=data.email, password=hash_password(data.password),premium_duration=now)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
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
            "token_type": "Bearer"
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error in register_user: {Exception}")

@router.post("/login")
def login_user(data:LoginUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password incorrect.")
    
    payload ={"id":user.id,"email":user.email}
    
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }

@router.post("/verify")
def refresh_token(data:TokenRefreshSchema):
    payload = verify_refresh_token(data.refresh_token)
    
    if payload is None:
        raise HTTPException(401, "Invalid refresh token")

    new_access = create_access_token({"id": payload["id"], "email": payload["email"]})

    return {"access_token": new_access, "token_type": "Bearer"}