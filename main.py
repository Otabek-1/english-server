from fastapi import FastAPI
from auth.router import router as auth_router

app = FastAPI(title="Server")

app.include_router(auth_router)

@app.get("/")
def root():
    return {"message":"Server is live!"}
