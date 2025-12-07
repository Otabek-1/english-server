from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .auth import hash_password, create_access_token, create_refresh_token, verify_password, verify_access_token, verify_refresh_token
from .schema import RegisterUser, LoginUser, TokenRefreshSchema
from database.db import get_db, User, Notification

router = APIRouter(prefix="/auth")

@router.post("/register")
def register_user(data: RegisterUser, db: Session = Depends(get_db)):
    email_exists = db.query(User).filter(User.email == data.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    try:
        new_user = User(username=data.username, email=data.email, password=hash_password(data.password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        access_token = create_access_token({"id":new_user.id,"email":new_user.email})
        refresh_token = create_refresh_token({"id":new_user.id,"email":new_user.email})
        welcome_notification = Notification(title=f"Xush kelibsiz, {new_user.username}! 👋",body=f"Bizning platformamizga qo'shilganingiz uchun tashakkur. Ingliz tili o'rganishni boshlang va o'z darajangizni oshiring!")
        db.add(welcome_notification)
        db.commit()
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