import os
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import desc, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from auth.auth import get_current_user
from auth.router import router as auth_router
from database.db import Feedback as FeedbackModel, SpeakingResult, User, WritingResult, get_db
from routes.News import router as news_router
from routes.ReadingMockQuestion import router as reading_routes
from routes.WritingMock import router as writing_router
from routes.dashboard_router import router as dashboard_router
from routes.ielts_router import router as ielts_router
from routes.listening_router import router as listening_router
from routes.notification_router import router as notification_routes
from routes.permissions_router import router as perm_router
from routes.session_router import router as session_router
from routes.speaking_router import router as speaking_router
from routes.traffic_monitor_router import router as traffic_monitor_router
from routes.tts_router import router as tts_router
from routes.user import router as user_router
from services.email_service import send_email
from services.request_monitor import create_audit_log, extract_client_ip, should_skip_logging
from database.db import SessionLocal

load_dotenv()

app = FastAPI(title="Server")

_session_secret = os.getenv("SESSION_SECRET_KEY")
if not _session_secret:
    raise ValueError(
        "SESSION_SECRET_KEY must be set in environment (e.g. a long random string)"
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(ielts_router)
app.include_router(dashboard_router)
app.include_router(traffic_monitor_router)


class mailModel(BaseModel):
    full_name: str
    email: str
    message: str


uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def root():
    return {"message": "Server is live!"}


@app.middleware("http")
async def request_audit_middleware(request, call_next):
    started_at = perf_counter()
    response = None
    try:
        response = await call_next(request)
    except Exception:
        response = Response(status_code=500)
        raise
    finally:
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        path = request.url.path
        if not should_skip_logging(path):
            headers = {key.lower(): value for key, value in request.headers.items()}
            client_ip, forwarded_for = extract_client_ip(headers, request.client.host if request.client else None)
            db = SessionLocal()
            try:
                try:
                    create_audit_log(
                        db,
                        method=request.method,
                        path=path,
                        query_string=request.url.query,
                        full_url=str(request.url),
                        status_code=response.status_code,
                        client_ip=client_ip,
                        forwarded_for=forwarded_for,
                        host=headers.get("host"),
                        origin=headers.get("origin"),
                        referer=headers.get("referer"),
                        user_agent=headers.get("user-agent"),
                        scheme=request.url.scheme,
                        request_headers={
                            "origin": headers.get("origin"),
                            "referer": headers.get("referer"),
                            "host": headers.get("host"),
                            "x_forwarded_for": forwarded_for,
                            "x_real_ip": headers.get("x-real-ip"),
                            "sec_fetch_site": headers.get("sec-fetch-site"),
                            "sec_fetch_mode": headers.get("sec-fetch-mode"),
                            "content_type": headers.get("content-type"),
                            "authorization_present": bool(headers.get("authorization")),
                            "request_time_ms": elapsed_ms,
                        },
                    )
                except Exception:
                    db.rollback()
            finally:
                db.close()
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "mockstream-server"}


@app.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "db": "ok",
        "features": {
            "google_oauth": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "supabase": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")),
            "mailjet": bool(
                os.getenv("MAILJET_API_KEY")
                and os.getenv("MAILJET_API_SECRET")
                and os.getenv("MAILJET_SENDER_EMAIL")
            ),
        },
    }


@app.post("/contact")
def contact(data: mailModel):
    msg = f"""
    Full name: {data.full_name}
    <br><br><br>
    Email: {data.email}
    <br><br><br>
    Message: {data.message}
    """

    contact_email = os.getenv("CONTACT_EMAIL", "davirbekkhasanov02@gmail.com")
    success, detail = send_email(
        to_email=contact_email,
        subject=f"Message from {data.full_name}",
        message=msg,
    )
    if not success:
        raise HTTPException(status_code=503, detail=f"Email service unavailable: {detail}")
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
    text: str
    rating: int


@app.post("/feedback")
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


@app.get("/feedback/me")
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


@app.get("/feedback/public")
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
