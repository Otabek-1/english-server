from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from auth.auth import verify_role
from database.db import get_db, WritingMock

router = APIRouter(prefix="/mock/writing", tags=["Writing", "Mock","CEFR"])

@router.get("/all")
def get_all_writings(db: Session = Depends(get_db)):
    data = db.query(WritingMock).all()
    return data

@router.get("/mock/{id}")
def get_by_id(id:int, db: Session = Depends(get_db)):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return exists

@router.post("/")
def create_mock():
    pass