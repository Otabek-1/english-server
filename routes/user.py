from fastapi import APIRouter, HTTPException, status, Depends
from database.db import get_db, User
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user, verify_password, hash_password
from schemas.userSchema import promoteData, udpateUser, passwordChange, premium
from datetime import datetime, timedelta

router = APIRouter(prefix="/user")

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting all users.")

@router.get("/me")
def get_me(db:Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.id == payload.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Error in getting user info.')

@router.post("/promote")
def promote_user(data:promoteData,db:Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    try:
        found_user = db.query(User).filter(User.id == data.id).first()
        if not found_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        found_user.role = "admin"
        db.commit()
        db.refresh(found_user)
        return {"message":"User promoted."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in promoting user.")

@router.post("/demote")
def demote_user(data:promoteData, db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    try:
        found_user = db.query(User).filter(User.id == data.id).first()
        if not found_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        found_user.role = "user"
        db.commit()
        db.refresh(found_user)
        return {"message":"User demoted."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in demoting user.")

@router.put("/update")
def update_user(data:udpateUser, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == payload.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.username = data.username
        user.email = data.email
        db.commit()
        db.refresh(user)
        return {"message":"User updated."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in updating user data.")

@router.post("/password")
def change_password(data:passwordChange, db: Session = Depends(get_db), payload = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.id == payload.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if not verify_password(data.old_password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")
        user.password = hash_password(data.new_password)
        db.commit()
        db.refresh(user)
        return {"message":"Password updated successfully."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in changing password.")

@router.post("/premium")
def func(data:premium, user = Depends(verify_role(['admin'])), db: Session = Depends(get_db)):
    try:
        user_found = db.query(User).filter(User.id == data.id).first()
        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        now = datetime.utcnow()
        if user_found.premium_duration and user_found.premium_duration > now:
            user_found.premium_duration += timedelta(days=30)
        else:
            user_found.premium_duration = now + timedelta(days=30)
        
        db.commit()
        db.refresh(user_found)

        return {
        "message": "Premium duration updated successfully.",
        "premium_until": user_found.premium_duration
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in premium function.")