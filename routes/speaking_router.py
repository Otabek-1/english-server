from database.db import SpeakingMock, SpeakingResult, User
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user
from database.db import get_db
from services.email_service import send_email
from datetime import datetime, timezone
import shutil
from pathlib import Path
import zipfile
import os
from services.telegram_bot import send_audio_zip_to_telegram  # ✍️ Siz buni yozishingiz kerak
from typing import List

router = APIRouter(prefix="/mock/speaking", tags=["Speaking", "Mock", "CEFR"])


# ===== GET ALL SPEAKING MOCKS =====
@router.get("/all")
def get_all_speaking_mocks(db: Session = Depends(get_db)):
    """Get all speaking mocks"""
    data = db.query(SpeakingMock).all()
    return data


# ===== GET MOCK BY ID =====
@router.get("/mock/{id}")
def get_mock_by_id(id: int, db: Session = Depends(get_db)):
    """Get speaking mock by ID"""
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
    """
    Create new speaking mock
    
    questions format:
    {
      "1.1": [...],
      "1.2": [...],
      "2": [...],
      "3": [...]
    }
    """
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
UPLOAD_BASE = Path("uploads/speaking")
UPLOAD_BASE.mkdir(parents=True, exist_ok=True)

@router.post("/submit")
async def submit_speaking_result(
    mock_id: int = Form(...),
    total_duration: int = Form(...),
    audios: List[UploadFile] = File(...),  # ✅ File — oxirida
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Mock mavjudligini tekshirish
    mock = db.query(SpeakingMock).filter(SpeakingMock.id == mock_id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found")

    # 2. Premium statusini tekshirish
    is_premium = False
    if current_user.premium_duration is not None:
        # UTC vaqtida solishtirish (agar saqlangan vaqt UTC bo'lsa)
        if current_user.premium_duration.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            is_premium = True

    # 3. Papka yaratish
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    folder_name = f"user{current_user.id}_mock{mock_id}_{timestamp}"
    user_dir = UPLOAD_BASE / folder_name
    user_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for audio in audios:
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            continue  # yoki raise HTTPException

        safe_filename = audio.filename.replace(" ", "_") if audio.filename else "audio.webm"
        file_path = user_dir / safe_filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        saved_paths.append(file_path)

    # 4. Agar premium bo'lmasa — ZIP yaratib Telegramga yuborish
    if not is_premium:
        zip_path = user_dir.with_suffix(".zip")
        try:
            with zipfile.ZipFile(zip_path, "w") as zf:
                for fp in saved_paths:
                    zf.write(fp, arcname=fp.name)
            
            caption = (
                f"Non-premium submission\n"
                f"User ID: {current_user.id}\n"
                f"Mock ID: {mock_id}\n"
                f"Time: {timestamp}"
            )
            send_audio_zip_to_telegram(zip_path, caption=caption)

        finally:
            # Mahalliy fayllarni tozalash
            if user_dir.exists():
                shutil.rmtree(user_dir)
            if zip_path.exists():
                os.remove(zip_path)

        recordings_data = {"status": "sent_to_telegram"}

    else:
        # Premium — fayllar saqlanib qoladi
        recordings_data = {"folder": str(user_dir)}

    # 5. DB ga yozish
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
        "is_premium": is_premium
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
@router.post("/check/{id}")
def check_result(
    id: int,
    evaluation: dict,
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    result = db.query(SpeakingResult).filter(SpeakingResult.id == id).first()
    if not result:
        raise HTTPException(404, "Result not found")

    # Foydalanuvchini tekshirish
    result_user = db.query(User).filter(User.id == result.user_id).first()
    is_premium = result_user.role == "premium" or result_user.is_premium

    # Agar premium bo'lsa va audio saqlangan bo'lsa
    if is_premium and result.recordings.get("folder"):
        folder_path = Path(result.recordings["folder"])
        if folder_path.exists():
            zip_path = folder_path.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, "w") as zf:
                for fp in folder_path.rglob("*"):
                    if fp.is_file():
                        zf.write(fp, arcname=fp.relative_to(folder_path.parent))

            caption = f"Premium user evaluation\nUser ID: {result.user_id}\nMock ID: {result.mock_id}\nEvaluated by admin"
            send_audio_zip_to_telegram(zip_path, caption=caption)
            # ZIP faylni keyin o'chirish mumkin

    # ... (sizning mavjud evaluation logikangizni qo'shing)

    result.evaluation = {
        "scores": evaluation.get("scores"),
        "band": evaluation.get("band"),
        "feedbacks": evaluation.get("feedbacks"),
        "evaluated_at": datetime.utcnow().isoformat()
    }

    db.commit()
    db.refresh(result)

    # Email yoki boshqa narsa...

    return {"message": "Evaluated and audio ZIP sent to archive channel"}

# ===== CHECK/EVALUATE RESULT (ADMIN ONLY) =====
@router.post("/check/{id}")
def check_result(
    id: int,
    evaluation: dict,  # {scores: {...}, feedback: {...}, send_email: bool}
    db: Session = Depends(get_db),
    user = Depends(verify_role(['admin']))
):
    """
    Evaluate speaking result
    
    evaluation format:
    {
      "scores": {
        "part1.1": 8,
        "part1.2": 7,
        "part2": 8,
        "part3": 7,
        "total": 30
      },
      "band": "B1",
      "feedbacks": {
        "part1.1": "Good pronunciation...",
        "part1.2": "Good fluency...",
        "part2": "Well structured...",
        "part3": "Good discussion..."
      },
      "send_email": True
    }
    """
    result = db.query(SpeakingResult).filter(SpeakingResult.id == id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")
    
    # Update result with evaluation
    result.evaluation = {
        "scores": evaluation.get("scores"),
        "band": evaluation.get("band"),
        "feedbacks": evaluation.get("feedbacks"),
        "evaluated_at": datetime.utcnow().isoformat()
    }
    
    # Send email if requested
    if evaluation.get("send_email"):
        result_user = db.query(User).filter(User.id == result.user_id).first()
        if result_user:
            mock_data = result.mock
            message = f"""
<html>
  <head>
    <style>
      body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        background-color: #f5f5f5;
      }}
      .container {{
        max-width: 600px;
        margin: 20px auto;
        background-color: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }}
      .header {{
        text-align: center;
        border-bottom: 3px solid #3498db;
        padding-bottom: 20px;
        margin-bottom: 30px;
      }}
      .header h1 {{
        color: #3498db;
        margin: 0;
        font-size: 28px;
      }}
      .header p {{
        color: #7f8c8d;
        margin: 5px 0 0 0;
        font-size: 14px;
      }}
      .score-box {{
        background-color: #ecf0f1;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
        border-left: 4px solid #3498db;
      }}
      .score-row {{
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #bdc3c7;
      }}
      .score-row:last-child {{
        border-bottom: none;
      }}
      .score-label {{
        font-weight: bold;
        color: #2c3e50;
      }}
      .score-value {{
        color: #3498db;
        font-weight: bold;
        font-size: 16px;
      }}
      .band-display {{
        text-align: center;
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        padding: 20px;
        border-radius: 5px;
        margin: 20px 0;
        font-size: 32px;
        font-weight: bold;
      }}
      .part-section {{
        background-color: #f9f9f9;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
        border-left: 4px solid #2ecc71;
      }}
      .part-title {{
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 8px;
        font-size: 16px;
      }}
      .part-score {{
        display: inline-block;
        background-color: #2ecc71;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin-bottom: 10px;
      }}
      .feedback-text {{
        color: #555;
        padding: 10px;
        background-color: white;
        border-radius: 3px;
        font-style: italic;
        border-left: 3px solid #f39c12;
      }}
      .footer {{
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #ecf0f1;
        text-align: center;
        color: #95a5a6;
        font-size: 12px;
      }}
      .evaluated-time {{
        color: #7f8c8d;
        font-size: 12px;
        margin-top: 10px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>🎤 Speaking Mock Review</h1>
        <p>Your assessment results are ready</p>
      </div>

      <div class="score-box">
        <div class="score-row">
          <span class="score-label">Mock ID:</span>
          <span>{mock_data.id}</span>
        </div>
        <div class="score-row">
          <span class="score-label">Total Score:</span>
          <span class="score-value">{evaluation.get("scores", {}).get("total", "N/A")}/40</span>
        </div>
      </div>

      <div class="band-display">
        {evaluation.get("band", "N/A")}
      </div>

      <div class="part-section">
        <div class="part-title">✓ Part 1.1 - Individual Long Turn</div>
        <div class="part-score">Score: {evaluation.get("scores", {}).get("part1.1", "N/A")}/10</div>
        <div class="feedback-text">
          {evaluation.get("feedbacks", {}).get("part1.1", "N/A")}
        </div>
      </div>

      <div class="part-section">
        <div class="part-title">✓ Part 1.2 - Picture Description</div>
        <div class="part-score">Score: {evaluation.get("scores", {}).get("part1.2", "N/A")}/10</div>
        <div class="feedback-text">
          {evaluation.get("feedbacks", {}).get("part1.2", "N/A")}
        </div>
      </div>

      <div class="part-section">
        <div class="part-title">✓ Part 2 - Extended Monologue</div>
        <div class="part-score">Score: {evaluation.get("scores", {}).get("part2", "N/A")}/10</div>
        <div class="feedback-text">
          {evaluation.get("feedbacks", {}).get("part2", "N/A")}
        </div>
      </div>

      <div class="part-section">
        <div class="part-title">✓ Part 3 - Discussion</div>
        <div class="part-score">Score: {evaluation.get("scores", {}).get("part3", "N/A")}/10</div>
        <div class="feedback-text">
          {evaluation.get("feedbacks", {}).get("part3", "N/A")}
        </div>
      </div>

      <div class="footer">
        <p>Thank you for taking the Speaking Mock test!</p>
        <div class="evaluated-time">
          Evaluated: {evaluation.get("evaluated_at", "N/A")}
        </div>
        <p style="margin-top: 15px; color: #bdc3c7;">
          © 2025 MockStream & CodeCraft
        </p>
      </div>
    </div>
  </body>
</html>
"""
            send_email(
                result_user.email,
                f"Speaking mock #{mock_data.id} evaluation results",
                message
            )
    
    db.commit()
    db.refresh(result)
    return {
        "message": "Result evaluated successfully.",
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
    evaluated = len([r for r in results if hasattr(r, 'evaluation') and r.evaluation])
    pending = total_submissions - evaluated
    
    avg_score = 0
    if evaluated > 0:
        scores = [r.evaluation.get("scores", {}).get("total", 0) for r in results if hasattr(r, 'evaluation') and r.evaluation]
        avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "mock_id": mock_id,
        "total_submissions": total_submissions,
        "evaluated": evaluated,
        "pending": pending,
        "average_score": round(avg_score, 2)
    }
