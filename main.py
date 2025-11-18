from fastapi import FastAPI
from auth.router import router as auth_router
from routes.user import router as user_router
from routes.ReadingMockQuestion import router as reading_routes

app = FastAPI(title="Server")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(reading_routes)

@app.get("/")
def root():
    return {"message":"Server is live!"}
