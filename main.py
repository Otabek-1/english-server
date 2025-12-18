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
from rate_limit import global_rate_limiter

app = FastAPI(title="Server")

# app.middleware("http")(global_rate_limiter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:5173","https://mockstream.netlify.app"],
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

# ===== STATIC FILES - Audio, Images, etc. =====
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message":"Server is live!"}