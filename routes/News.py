from database.db import news, User, get_db
from auth.auth import verify_role, get_current_user
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
def react(
    id: int,
    data: React,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Yangilikni topish
    exists = db.query(news).filter(news.id == id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Not found.")

    # reactions - dict bo'lishi kerak
    reactions = exists.reactions or {}          # { "👍": [1,2], "❤️": [5], ... }

    # 1️⃣ Barcha reactionlardan userni olib tashlaymiz (unreact)
    for emoji, users in reactions.items():
        if user.id in users:
            users.remove(user.id)

    # 2️⃣ Agar yangi emoji YAQINDA bosilgan bo‘lsa → unreact bo‘lgan, qaytadan qo‘shmaymiz
    #    Ya'ni shu emoji ostida user bo‘lmasa, qo‘shib qo‘yamiz
    if user.id not in reactions.get(data.emoji, []):
        # agar bu emoji hali yo‘q bo‘lsa → massiv ochamiz
        reactions.setdefault(data.emoji, [])
        reactions[data.emoji].append(user.id)

    # Yangilash
    exists.reactions = reactions
    db.commit()
    db.refresh(exists)

    return {"message": "Success", "reactions": reactions}


@router.delete("/{id}")
def delete(id:int, db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(news).filter(news.id==id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(exists)
    db.commit()
    return {"message":"Success"}