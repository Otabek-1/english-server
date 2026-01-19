from database.db import SpeakingMock, SpeakingResult, User
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user
from database.db import get_db
from services.email_service import send_email
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import List
import zipfile
import io
from supabase import create_client, Client
from services.telegram_bot import send_audio_zip_to_telegram
import requests

router = APIRouter(prefix="/mock/speaking", tags=["Speaking", "Mock", "CEFR"])

# ===== SUPABASE CLIENT =====
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "speaking-audios"


# ===== GET ALL SPEAKING MOCKS =====
@router.get("/all")
def get_all_speaking_mocks(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Get all speaking mocks - authenticated users only"""
    data = db.query(SpeakingMock).all()
    return data


# ===== GET MOCK BY ID =====
@router.get("/mock/{id}")
def get_mock_by_id(id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Get speaking mock by ID - authenticated users only"""
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == id).first()
    if not mock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock not found.")
    return mock


# ===== CREATE SPEAKING MOCK (ADMIN ONLY) =====
@router.post("/create")
def create_speaking_mock(
    title: str,
    questions: dict,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """Create new speaking mock"""
    mock = SpeakingMock(title=title, questions=questions)
    db.add(mock)
    db.commit()
    db.refresh(mock)
    return {"message": "Mock created successfully.", "mock": mock}


# ===== UPDATE SPEAKING MOCK (ADMIN ONLY) =====
@router.put("/update/{id}")
def update_speaking_mock(
    id: int,
    title: str = None,
    questions: dict = None,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """Update speaking mock"""
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == id).first()
    if not mock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock not found.")
    
    if title:
        mock.title = title
    if questions:
        mock.questions = questions
    
    db.commit()
    db.refresh(mock)
    return {"message": "Updated successfully.", "mock": mock}


# ===== DELETE SPEAKING MOCK (ADMIN ONLY) =====
@router.delete("/delete/{id}")
def delete_speaking_mock(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """Delete speaking mock"""
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == id).first()
    if not mock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock not found.")
    
    db.delete(mock)
    db.commit()
    return {"message": "Deleted successfully."}


# ===== SUBMIT SPEAKING RESULT =====
@router.post("/submit")
async def submit_speaking_result(
    mock_id: int = Form(...),
    total_duration: int = Form(...),
    audios: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit speaking exam result with audio files to Supabase"""
    
    # 1. Mock mavjudligini tekshirish
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == mock_id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    # 2. Premium statusini tekshirish
    is_premium = False
    if current_user.premium_duration is not None:
        if current_user.premium_duration.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            is_premium = True

    # 3. Timestamp va folder path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    folder_name = f"user{current_user.id}_mock{mock_id}_{timestamp}"
    
    # 4. Supabase'ga upload qilish
    recordings_data = {}
    try:
        for audio in audios:
            if not audio.content_type or not audio.content_type.startswith("audio/"):
                continue

            safe_filename = audio.filename.replace(" ", "_") if audio.filename else "audio.webm"
            file_path = f"{folder_name}/{safe_filename}"
            
            # Supabase'ga upload
            file_content = await audio.read()
            supabase.storage.from_(BUCKET_NAME).upload(
                file_path,
                file_content,
                {"content_type": audio.content_type}
            )
            
            # Public URL olish
            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            recordings_data[safe_filename.replace('.webm', '')] = public_url
    
    except Exception as e:
        print(f"Supabase upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # 5. Agar non-premium bo'lsa, ZIP yaratib Telegramga yuborish
    if not is_premium:
        try:
            # ZIP memory'da yaratish
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for key, url in recordings_data.items():
                    # URL'dan audio download qilish
                    response = requests.get(url)
                    if response.status_code == 200:
                        zf.writestr(f"{key}.webm", response.content)
            
            zip_buffer.seek(0)
            
            caption = (
                f"📱 Non-premium Submission\n"
                f"👤 User ID: {current_user.id}\n"
                f"📝 Mock ID: {mock_id}\n"
                f"⏰ Time: {timestamp}"
            )
            send_audio_zip_to_telegram(zip_buffer, caption=caption)
        
        except Exception as e:
            print(f"Telegram send error: {e}")
        
        # Non-premium'lar uchun Supabase'dagi audiolari o'chirish
        try:
            for key in recordings_data.keys():
                file_path = f"{folder_name}/{key}.webm"
                supabase.storage.from_(BUCKET_NAME).remove([file_path])
        except Exception as e:
            print(f"Supabase delete error: {e}")
        
        recordings_data = {"status": "sent_to_telegram"}

    else:
        # Premium - Supabase URL'larni saqla
        recordings_data = {"folder": folder_name, "audios": recordings_data}

    # 6. DB ga yozish
    result = SpeakingResult(
        user_id=current_user.id,
        mock_id=mock_id,
        recordings=recordings_data,
        total_duration=total_duration
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "message": "Submitted successfully",
        "result_id": result.id,
        "is_premium": is_premium,
        "storage_type": "supabase" if is_premium else "telegram_archive"
    }

from pydantic import BaseModel
from typing import List, Dict
import base64

# ===== PYDANTIC MODEL FOR MOBILE =====
class MobileAudioData(BaseModel):
    question_id: str
    base64_audio: str  # base64 encoded audio

class MobileSubmitRequest(BaseModel):
    mock_id: int
    total_duration: int
    audios: List[MobileAudioData]

@router.post("/submit-mobile")
async def submit_speaking_result_mobile(
    request: MobileSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit speaking exam result from mobile app with base64 encoded audio files"""
    
    mock_id = request.mock_id
    total_duration = request.total_duration
    audios = request.audios
    
    # 1. Mock mavjudligini tekshirish
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == mock_id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    # 2. Premium statusini tekshirish
    is_premium = False
    if current_user.premium_duration is not None:
        if current_user.premium_duration.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            is_premium = True

    # 3. Timestamp va folder path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    folder_name = f"user{current_user.id}_mock{mock_id}_{timestamp}"
    
    # 4. Supabase'ga upload qilish (base64 dan)
    recordings_data = {}
    try:
        for audio_data in audios:
            try:
                # Base64 decode
                audio_bytes = base64.b64decode(audio_data.base64_audio)
                
                safe_filename = f"{audio_data.question_id}.m4a"
                file_path = f"{folder_name}/{safe_filename}"
                
                # Supabase'ga upload
                supabase.storage.from_(BUCKET_NAME).upload(
                    file_path,
                    audio_bytes,
                    {"content_type": "audio/mp4"}
                )
                
                # Public URL olish
                public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
                recordings_data[audio_data.question_id] = public_url
                
                print(f"✅ Uploaded: {safe_filename}")
            
            except Exception as audio_err:
                print(f"❌ Error uploading {audio_data.question_id}: {audio_err}")
                # Continue with other files
                continue
    
    except Exception as e:
        print(f"Supabase upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # 5. Agar non-premium bo'lsa, ZIP yaratib Telegramga yuborish
    if not is_premium:
        try:
            # ZIP memory'da yaratish
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for key, url in recordings_data.items():
                    # URL'dan audio download qilish
                    response = requests.get(url)
                    if response.status_code == 200:
                        zf.writestr(f"{key}.m4a", response.content)
            
            zip_buffer.seek(0)
            
            caption = (
                f"📱 Mobile Non-premium Submission\n"
                f"👤 User ID: {current_user.id}\n"
                f"📝 Mock ID: {mock_id}\n"
                f"⏰ Time: {timestamp}"
            )
            send_audio_zip_to_telegram(zip_buffer, caption=caption)
        
        except Exception as e:
            print(f"Telegram send error: {e}")
        
        # Non-premium'lar uchun Supabase'dagi audiolari o'chirish
        try:
            for key in recordings_data.keys():
                file_path = f"{folder_name}/{key}.m4a"
                supabase.storage.from_(BUCKET_NAME).remove([file_path])
        except Exception as e:
            print(f"Supabase delete error: {e}")
        
        recordings_data = {"status": "sent_to_telegram"}

    else:
        # Premium - Supabase URL'larni saqla
        recordings_data = {"folder": folder_name, "audios": recordings_data}

    # 6. DB ga yozish
    result = SpeakingResult(
        user_id=current_user.id,
        mock_id=mock_id,
        recordings=recordings_data,
        total_duration=total_duration
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "message": "Submitted successfully from mobile",
        "result_id": result.id,
        "is_premium": is_premium,
        "storage_type": "supabase" if is_premium else "telegram_archive",
        "files_uploaded": len(recordings_data)
    }
    
    
# ===== GET ALL RESULTS (ADMIN ONLY) =====
@router.get("/results")
def get_all_results(
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """Get all speaking results"""
    results = db.query(SpeakingResult).all()
    return results


# ===== GET RESULTS BY USER =====
@router.get("/results/user/{user_id}")
def get_user_results(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get results by user ID (user can only see their own)"""
    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    
    results = db.query(SpeakingResult).filter(SpeakingResult.user_id == user_id).all()
    return results


# ===== GET RESULT BY ID =====
@router.get("/result/{id}")
def get_result_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get result by ID"""
    result = db.query(SpeakingResult).filter(SpeakingResult.id == id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")
    
    # Check authorization
    if result.user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    
    return {"result": result}


# ===== CHECK/EVALUATE RESULT (ADMIN ONLY) =====
@router.post("/check/{id}")
def check_result(
    id: int,
    evaluation: dict,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    # ===== 0. Result mavjudligini tekshirish =====
    result = db.query(SpeakingResult).filter(SpeakingResult.id == id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    result_user = db.query(User).filter(User.id == result.user_id).first()

    # ===== 1. ZIP qilib Telegramga yuborish =====
    if result.recordings and "audios" in result.recordings:
        try:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for key, url in result.recordings["audios"].items():
                    r = requests.get(url)
                    if r.status_code == 200:
                        zf.writestr(f"{key}.webm", r.content)

            zip_buffer.seek(0)

            caption = (
                f"✅ Speaking Checked\n"
                f"👤 User ID: {result.user_id}\n"
                f"📝 Mock ID: {result.mock_id}\n"
                f"🏆 Band: {evaluation.get('band')}\n"
                f"📊 Total: {evaluation.get('scores', {}).get('total')}/40"
            )

            send_audio_zip_to_telegram(zip_buffer, caption)

        except Exception as e:
            print("Telegram ZIP error:", e)

    # ===== 2. SUPABASE'DAN FOLDER + FILE'LARNI O‘CHIRISH =====
    folder_name = result.recordings.get("folder") if result.recordings else None

    if folder_name:
        try:
            files = supabase.storage.from_(BUCKET_NAME).list(folder_name)
            paths = [f"{folder_name}/{f['name']}" for f in files]

            if paths:
                supabase.storage.from_(BUCKET_NAME).remove(paths)

        except Exception as e:
            print("Supabase delete error:", e)



    # ===== 4. EVALUATION SAQLASH =====
    result.evaluation = {
        "scores": evaluation.get("scores"),
        "band": evaluation.get("band"),
        "feedbacks": evaluation.get("feedbacks"),
        "evaluated_at": datetime.utcnow().isoformat(),
        "audio_archived": True
    }

    # ===== 5. EMAIL YUBORISH =====
    if evaluation.get("send_email") and result_user:
        scores = evaluation.get("scores", {})
        feedbacks = evaluation.get("feedbacks", {})

        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#f5f5f5;">
          <div style="max-width:700px;margin:auto;background:#fff;padding:30px;border-radius:8px;">
            <h2 style="color:#3498db;">🎤 Speaking Mock Evaluation</h2>

            <p><strong>Mock ID:</strong> {result.mock_id}</p>
            <p><strong>Overall Band:</strong> {evaluation.get('band')}</p>
            <p><strong>Total Score:</strong> {scores.get('total')}/40</p>

            <hr>

            <h3>Detailed Feedback</h3>

            <p><strong>Part 1.1:</strong> {scores.get('part1.1')}/10</p>
            <p>{feedbacks.get('part1.1')}</p>

            <p><strong>Part 1.2:</strong> {scores.get('part1.2')}/10</p>
            <p>{feedbacks.get('part1.2')}</p>

            <p><strong>Part 2:</strong> {scores.get('part2')}/10</p>
            <p>{feedbacks.get('part2')}</p>

            <p><strong>Part 3:</strong> {scores.get('part3')}/10</p>
            <p>{feedbacks.get('part3')}</p>

            <hr>
            <p style="color:#888;font-size:12px;">
              Your audio recordings have been securely reviewed and removed from storage.
            </p>

            <p style="font-size:12px;color:#aaa;">© 2025 MockStream</p>
          </div>
        </body>
        </html>
        """

        try:
            send_email(
                result_user.email,
                f"🎤 Speaking Mock #{result.mock_id} – Evaluation Result",
                email_html
            )
        except Exception as e:
            print("Email send error:", e)
    # ===== 3. RECORDINGS NI DB'DAN TOZALASH =====
    db.delete(result)

    # ===== 6. DB COMMIT =====
    db.commit()

    return {
        "message": "Result checked, archived, deleted & emailed successfully",
        "result_id": result.id,
        "band": evaluation.get("band"),
        "total_score": evaluation.get("scores", {}).get("total")
    }


# ===== GET RESULT STATISTICS (ADMIN ONLY) =====
@router.get("/stats/mock/{mock_id}")
def get_mock_statistics(
    mock_id: int,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """Get statistics for a specific mock"""
    results = db.query(SpeakingResult).filter(SpeakingResult.mock_id == mock_id).all()
    
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No results found.")
    
    total_submissions = len(results)
    evaluated = len([r for r in results if r.evaluation is not None])
    pending = total_submissions - evaluated
    
    avg_score = 0
    if evaluated > 0:
        scores = [r.evaluation.get("scores", {}).get("total", 0) for r in results if r.evaluation]
        avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "mock_id": mock_id,
        "total_submissions": total_submissions,
        "evaluated": evaluated,
        "pending": pending,
        "average_score": round(avg_score, 2)
    }