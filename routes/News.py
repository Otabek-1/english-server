from database.db import news, User, get_db
from auth.auth import verify_role, verify_access_token
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.news_schema import News, React
from collections import defaultdict

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/")
def get_news(db: Session = Depends(get_db)):
    res = db.query(news).all()
    return res

@router.get("/{slug}")
def get_by_slug(slug:str,db: Session = Depends(get_db)):
    res = db.query(news).filter(news.slug == slug).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return res

def slugify(text: str):
    letters="abcdefghijklmnopqrstuvwxyz"
    res=""
    for i in text:
        if i.lower() in letters:
            res+=i
        elif i == " ":
            res+="-"
    return res
    
@router.post("/create")
def create_news(data:News, db: Session = Depends(get_db), user= Depends(verify_role(["admin"]))):
    new = news(title=data.title, body=data.body,slug=slugify(data.title))
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.put("/{id}")
def update_new(id:int,data: News, db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(news).filter(news.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    exists.title = data.title
    exists.body = data.body
    exists.slug = slugify(data.title)
    db.commit()
    db.refresh(exists)
    return exists

@router.post("/react/{id}")
def react(id:int, data: React, db: Session = Depends(get_db), user = verify_access_token):
    exists = db.query(news).filter(news.id==id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    reactions = defaultdict(exists.reactions)
    reactions[data.emoji].append(user.id)
    exists.reactions = reactions
    db.commit()
    db.refresh(exists)
    return {"message":"Success"}

@router.delete("/{id}")
def delete(id:int, db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(news).filter(news.id==id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(exists)
    db.commit()
    return {"message":"Success"}