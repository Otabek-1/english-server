from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_router
from routes.user import router as user_router
from routes.ReadingMockQuestion import router as reading_routes
from rate_limit import global_rate_limiter

app = FastAPI(title="Server")

app.middleware("http")(global_rate_limiter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(reading_routes)

@app.get("/")
def root():
    return {"message":"Server is live!"}