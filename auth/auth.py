import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
load_dotenv()

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

def hash_password(psw: str) -> str:
    return pwd_context.hash(psw)

def verify_password(plain_psw: str, hashed_psw: str) -> bool:
    return pwd_context.verify(plain_psw, hashed_psw)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm="HS256")

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, os.getenv("REFRESH_SECRET_KEY"), algorithm="HS256")

def verify_access_token(token:str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except:
        return None

def verify_refresh_token(token:str):
    try:
        payload = jwt.decode(token, os.getenv("REFRESH_SECRET_KEY"), algorithms=["HS256"])
        return payload
    except:
        return None

