from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from auth.router import router as auth_router
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

app = FastAPI(title="Server")

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