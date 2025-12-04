from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from auth.auth import verify_role, verify_access_token
from database.db import get_db, WritingMock, WritingResult
from schemas.WritingMockSchema import CreateMockData, MockResponse, Result

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

@router.post("/create")
def create_mock(data:CreateMockData, db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    mock = WritingMock(images=data.images,task1=data.task1,task2=data.task2)
    db.add(mock)
    db.commit()
    db.refresh(mock)
    return {"message":"Mock created successfully.", "mock":mock}

@router.put("/update/{id}")
def update_mock(id: int, data:CreateMockData,db:Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    exists.images = data.images
    exists.task1 = data.task1
    exists.task2 = data.task2
    db.commit()
    db.refresh(exists)
    return {"message":"Updated successfully."}

@router.delete("/delete/{id}")
def delete_mock(id:int, db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(exists)
    db.commit()
    return {"message":"Deleted successfully."}

@router.post("/submit")
def submit_mock(data: MockResponse,db:Session = Depends(get_db), user = Depends(verify_access_token)):
    result = WritingResult(user_id = user["id"], task1= data.task1, task2=data.task2,mock_id=data.mock_id)
    db.add(result)
    db.commit()
    db.refresh(result)
    return {"message":"Accepted successfully."}

@router.get("/results")
def get_all_results(db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    res = db.query(WritingResult).all()
    return res

@router.get("/result/{id}")
def get_result_by_id(id:int, db:Session = Depends(get_db), user = Depends(verify_access_token)):
    exists = db.query(WritingResult).filter(WritingResult.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return {"mock":exists}

@router.post("/check/{id}")
def check_result(id:int,data:Result, db:Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(WritingResult).filter(WritingResult.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    exists.result = data.result
    db.commit()
    db.refresh(exists)
    return {"message":"Checked successfully."}
