from fastapi import APIRouter, HTTPException, status, Depends
from database.db import get_db, User
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user, verify_password, hash_password
from schemas.userSchema import promoteData, udpateUser, passwordChange, premium
from datetime import datetime, timedelta
from sqlalchemy import or_

router = APIRouter(prefix="/user")

RAMADAN_PREMIUM_UNTIL = datetime(datetime.utcnow().year, 5, 1, 23, 59, 59)

@router.get("/users")
def get_users(db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting all users.")

@router.get("/id/{user_id}")
def get_user_by_platform_id(
    user_id: int,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    try:
        found_user = db.query(User).filter(User.id == user_id).first()
        if not found_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return {
            "id": found_user.id,
            "username": found_user.username,
            "email": found_user.email,
            "role": found_user.role,
            "google_avatar": found_user.google_avatar,
            "premium_duration": found_user.premium_duration
        }
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting user by ID.")

@router.get("/me")
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in getting user info.")

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
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in demoting user.")

@router.put("/update")
def update_user(data: udpateUser, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.username = data.username
        user.email = data.email
        db.commit()
        db.refresh(user)
        return {"message": "User updated."}
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in updating user data.")

@router.post("/password")
def change_password(data: passwordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if not verify_password(data.old_password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")
        user.password = hash_password(data.new_password)
        db.commit()
        db.refresh(user)
        return {"message": "Password updated successfully."}
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in premium function.")

@router.post("/premium/remove")
def remove_premium(data: premium, user = Depends(verify_role(['admin'])), db: Session = Depends(get_db)):
    try:
        user_found = db.query(User).filter(User.id == data.id).first()
        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user_found.premium_duration = None
        db.commit()
        db.refresh(user_found)
        return {
            "message": "Premium removed successfully.",
            "premium_until": user_found.premium_duration
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in remove premium function.")

@router.post("/premium/ramadan-grant")
def grant_ramadan_premium_for_all(user = Depends(verify_role(['admin'])), db: Session = Depends(get_db)):
    try:
        updated_count = (
            db.query(User)
            .filter(
                or_(
                    User.premium_duration.is_(None),
                    User.premium_duration < RAMADAN_PREMIUM_UNTIL
                )
            )
            .update({User.premium_duration: RAMADAN_PREMIUM_UNTIL}, synchronize_session=False)
        )
        db.commit()
        return {
            "message": "Ramadan premium granted.",
            "premium_until": RAMADAN_PREMIUM_UNTIL,
            "updated_users": updated_count
        }
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in ramadan premium bulk grant."
        )

