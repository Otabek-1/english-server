from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
from services.email_service import send_email
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from database.db import Feedback as FeedbackModel, SpeakingResult, WritingResult, get_db, User
import os


app = FastAPI(title="Server")
load_dotenv()

_session_secret = os.getenv("SESSION_SECRET_KEY")
if not _session_secret:
    raise ValueError(
        "SESSION_SECRET_KEY must be set in environment (e.g. a long random string)"
    )
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret,
)

# CORS ochiq — public route'lar (gTTS va b.) boshqa loyihalardan ham ishlatiladi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    contact_email = os.getenv("CONTACT_EMAIL", "davirbekkhasanov02@gmail.com")
    send_email(to_email=contact_email, subject=f"Message from {data.full_name}", message=msg)
    return {"success": True}


class keyData(BaseModel):
    password: str


@app.post("/key")
def get_key(data: keyData):
    key_password = os.getenv("KEY_PASSWORD")
    if not key_password or data.password != key_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")
    return {"key": gemini_key}

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

@app.get('/feedback/me')
def get_my_feedback_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feedbacks = (
        db.query(FeedbackModel)
        .filter(FeedbackModel.user_id == current_user.id)
        .order_by(FeedbackModel.id.desc())
        .all()
    )
    writing_count = db.query(WritingResult).filter(WritingResult.user_id == current_user.id).count()
    speaking_count = db.query(SpeakingResult).filter(SpeakingResult.user_id == current_user.id).count()

    return {
        "has_feedback": len(feedbacks) > 0,
        "mock_submissions_count": writing_count + speaking_count,
        "feedbacks": [
            {
                "id": item.id,
                "rating": item.rating,
                "text": item.text,
            }
            for item in feedbacks
        ],
    }

@app.get('/feedback/public')
def get_public_feedbacks(
    limit: int = 12,
    db: Session = Depends(get_db),
):
    safe_limit = max(1, min(limit, 30))
    rows = (
        db.query(FeedbackModel, User)
        .join(User, User.id == FeedbackModel.user_id)
        .filter(FeedbackModel.text.isnot(None))
        .filter(FeedbackModel.text != "")
        .order_by(desc(FeedbackModel.id))
        .limit(safe_limit)
        .all()
    )

    return {
        "feedbacks": [
            {
                "id": feedback.id,
                "username": user.username or "User",
                "rating": feedback.rating,
                "text": feedback.text,
            }
            for feedback, user in rows
        ]
    }
