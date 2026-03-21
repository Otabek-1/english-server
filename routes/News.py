import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.auth import get_current_user, verify_role
from database.db import get_db, news
from schemas.news_schema import News, React

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/")
def get_news(db: Session = Depends(get_db)):
    return db.query(news).all()


@router.get("/{slug}")
def get_by_slug(slug: str, db: Session = Depends(get_db)):
    res = db.query(news).filter(news.slug == slug).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return res


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return normalized.strip("-") or "news"


def build_unique_slug(db: Session, title: str, existing_id: int | None = None) -> str:
    base_slug = slugify(title)
    slug = base_slug
    index = 2

    while True:
        query = db.query(news).filter(news.slug == slug)
        if existing_id is not None:
            query = query.filter(news.id != existing_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{index}"
        index += 1


@router.post("/create")
def create_news(
    data: News,
    db: Session = Depends(get_db),
    _: object = Depends(verify_role(["admin"])),
):
    new = news(title=data.title, body=data.body, slug=build_unique_slug(db, data.title))
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.put("/{id}")
def update_new(
    id: int,
    data: News,
    db: Session = Depends(get_db),
    _: object = Depends(verify_role(["admin"])),
):
    exists = db.query(news).filter(news.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    exists.title = data.title
    exists.body = data.body
    exists.slug = build_unique_slug(db, data.title, existing_id=id)
    db.commit()
    db.refresh(exists)
    return exists


@router.post("/react/{id}")
def react(
    id: int,
    data: React,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    exists = db.query(news).filter(news.id == id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Not found.")

    reactions = exists.reactions or {}

    for _, users in reactions.items():
        if user.id in users:
            users.remove(user.id)

    if user.id not in reactions.get(data.emoji, []):
        reactions.setdefault(data.emoji, [])
        reactions[data.emoji].append(user.id)

    exists.reactions = reactions
    db.commit()
    db.refresh(exists)

    return {"message": "Success", "reactions": reactions}


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    _: object = Depends(verify_role(["admin"])),
):
    exists = db.query(news).filter(news.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(exists)
    db.commit()
    return {"message": "Success"}
