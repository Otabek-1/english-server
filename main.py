from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
from auth.router import router as auth_router
from auth.auth import get_current_user
from routes.user import router as user_router
from routes.ReadingMockQuestion import router as reading_routes
from routes.WritingMock import router as writing_router
from routes.notification_router import router as notification_routes
from routes.News import router as news_router
from routes.speaking_router import router as speaking_router
from routes.tts_router import router as tts_router
from routes.listening_router import router as listening_router
from routes.permissions_router import router as perm_router
from routes.session_router import router as session_router
from rate_limit import global_rate_limiter
from services.email_service import send_email
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database.db import Feedback as FeedbackModel, get_db, User
import os


app = FastAPI(title="Server")
load_dotenv()

app.add_middleware(
    SessionMiddleware,
    secret_key="allakakachiffejsfljgkldngkjgnksrjkngrjk32"
)

# app.middleware("http")(global_rate_limiter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ===== ROUTERS =====
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(reading_routes)
app.include_router(writing_router)
app.include_router(notification_routes)
app.include_router(news_router)
app.include_router(speaking_router)
app.include_router(tts_router)
app.include_router(listening_router)
app.include_router(perm_router)
app.include_router(session_router)

class mailModel(BaseModel):
    full_name:str
    email:str
    message:str



# ===== STATIC FILES - Audio, Images, etc. =====
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message":"Server is live!"}

@app.post('/contact')
def contact(data:mailModel):
    msg = f"""
    Full name: {data.full_name}
    <br><br><br>
    Email: {data.email}
    <br><br><br>
    Message: {data.message}
    """
    
    send_email(to_email="davirbekkhasanov02@gmail.com", subject=f"Message from {data.full_name}",message=msg)
    return {"success":True}

class keyData(BaseModel):
    password:str

@app.post('/key')
def get_key(data:keyData):
    if data.password == 'mocksTream10010512111111497':
        return {'key': os.getenv("GEMINI_API_KEY")}

class FeedbackCreate(BaseModel):
    text:str
    rating:int

@app.post('/feedback')
def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    feedback = FeedbackModel(
        user_id=current_user.id,
        rating=data.rating,
        text=data.text,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "success": True,
        "feedback_id": feedback.id,
        "user_id": feedback.user_id,
    }
