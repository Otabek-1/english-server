from fastapi import APIRouter, Depends
from database.db import get_db, Permissions
from auth.auth import verify_role
from sqlalchemy.orm import Session
from schemas.PermissionsSchema import data

router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get('/')
def get_all_permissions(db:Session = Depends(get_db)):
    res = db.query(Permissions).all()
    return res

@router.get("/{user_id}")
def user_permissions(user_id:int,db: Session = Depends(get_db)):
    res = db.query(Permissions).filter(Permissions.user_id == user_id).first()
    if not res:
        return {"data":"not_added"}
    return {"data":res}

@router.post("/{user_id}")
def add_permission(user_id:int, data:data, db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    new = Permissions(user_id=user_id,permissions = data.permissions)
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"message":"Success"}

@router.put("/{user_id}")
def update_permissions(user_id:int, data:data, db: Session = Depends(get_db),user = Depends(verify_role(['admin']))):
    res = db.query(Permissions).filter(Permissions.user_id == user_id).first()
    res.permissions = data.permissions
    db.commit()
    db.refresh(res)
    return {'message':"Success"}

@router.delete("/{user_id}")
def delete_permission(user_id:int, db: Session = Depends(get_db)):
    res=  db.query(Permissions).filter(Permissions.user_id==user_id).first()
    db.delete(res)
    db.commit()
    return {"message":"Success"}