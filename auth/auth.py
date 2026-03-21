import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.db import User, get_db

load_dotenv()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def hash_password(psw: str) -> str:
    return pwd_context.hash(psw)


def verify_password(plain_psw: str, hashed_psw: str) -> bool:
    return pwd_context.verify(plain_psw, hashed_psw)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _require_env("SECRET_KEY"), algorithm="HS256")


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _require_env("REFRESH_SECRET_KEY"), algorithm="HS256")


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, _require_env("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except Exception:
        return None


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, _require_env("REFRESH_SECRET_KEY"), algorithms=["HS256"])
        return payload
    except Exception:
        return None


def verify_role(roles: list):
    def role_checker(
        payload: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user_id = payload.id
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Access forbidden")

        return user

    return role_checker


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.id == payload["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
