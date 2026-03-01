from fastapi import APIRouter, Depends, status, HTTPException
from database.db import get_db, User, ListeningMock, ListeningMockAnswer
from auth.auth import verify_access_token, verify_role, get_current_user
from schemas.listeningSchema import ListeningMockSchema, ListeningMockAnswersSchema, ListeningSubmitSchema
from sqlalchemy.orm import Session
from services.telegram_bot import send_document_to_telegram
from datetime import datetime
from html import escape
import io
import os
import json

router = APIRouter(prefix="/cefr/listening", tags=["Listening"])

@router.get("/all")
def get_all_mocks(db:Session = Depends(get_db), user = Depends(get_current_user)):
    res = db.query(ListeningMock).all()
    return res

@router.get("/{id}")
def get_listening(id:int,db: Session = Depends(get_db), user = Depends(get_current_user)):
    res = db.query(ListeningMock).filter(ListeningMock.id == id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Listening mock not found")
    return res

@router.post("/create")
def add_mock(data:ListeningMockSchema,db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    new = ListeningMock(title=data.title,data=data.data,audio_part_1=data.audio_part_1,audio_part_2=data.audio_part_2,audio_part_3=data.audio_part_3,audio_part_4=data.audio_part_4,audio_part_5=data.audio_part_5,audio_part_6=data.audio_part_6)
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"message":"Success","id":new.id}

@router.put("/update/{id}")
def update_mock(id:int,data: ListeningMockSchema, db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    res = db.query(ListeningMock).filter(ListeningMock.id == id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Listening mock not found")
    res.title = data.title
    res.data = data.data
    res.audio_part_1 = data.audio_part_1
    res.audio_part_2 = data.audio_part_2
    res.audio_part_3 = data.audio_part_3
    res.audio_part_4 = data.audio_part_4
    res.audio_part_5 = data.audio_part_5
    res.audio_part_6 = data.audio_part_6
    db.commit()
    db.refresh(res)
    return {"message":"Success"}

@router.delete("/mock/{id}")
def delete_mock(
    id: int,
    user=Depends(verify_role(["admin"])),
    db: Session = Depends(get_db)
):
    res = db.query(ListeningMock).filter(ListeningMock.id == id).first()
    if not res:
        raise HTTPException(404, "Mock not found")

    ans = db.query(ListeningMockAnswer)\
        .filter(ListeningMockAnswer.mock_id == id)\
        .first()

    if ans:
        db.delete(ans)

    db.delete(res)
    db.commit()
    return {"message": "Success"}


# ANSWER CRUD
@router.get("/answer/{mock_id}")
def get_by_mock_id(mock_id:int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    res=  db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == mock_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Listening answers not found")
    return res

@router.post("/answer/create/{mock_id}")
def add_answer(mock_id:int, data:ListeningMockAnswersSchema ,db: Session = Depends(get_db), user=Depends(verify_role(["admin"]))):
    mock = db.query(ListeningMock).filter(ListeningMock.id == mock_id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Listening mock not found")

    existing = db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == mock_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Answers already exist for this mock")

    new = ListeningMockAnswer(mock_id=mock_id, part_1=data.part_1,part_2=data.part_2,part_3=data.part_3,part_4=data.part_4,part_5=data.part_5,part_6=data.part_6)
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"message":"Success"}

@router.put("/answer/update/{mock_id}")
def update_answers(mock_id:int, data: ListeningMockAnswersSchema, db: Session = Depends(get_db), user=Depends(verify_role(['admin']))):
    res = db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == mock_id).first()
    if not res:
        # Upsert behavior: editing old mocks without answer row should not crash
        res = ListeningMockAnswer(
            mock_id=mock_id,
            part_1=data.part_1,
            part_2=data.part_2,
            part_3=data.part_3,
            part_4=data.part_4,
            part_5=data.part_5,
            part_6=data.part_6,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return {"message":"Success"}

    res.part_1 = data.part_1
    res.part_2 = data.part_2
    res.part_3 = data.part_3
    res.part_4 = data.part_4
    res.part_5 = data.part_5
    res.part_6 = data.part_6
    db.commit()
    db.refresh(res)
    return {"message":"Success"}


@router.post("/submit")
def submit_listening(
    data: ListeningSubmitSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mock = db.query(ListeningMock).filter(ListeningMock.id == data.mock_id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Listening mock not found")

    answer_obj = db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == data.mock_id).first()
    if not answer_obj:
        raise HTTPException(status_code=404, detail="Listening answers not found")

    def normalize(value):
        if value is None:
            return ""
        return str(value).strip().lower()

    user_parts = {
        "part1": data.part1 or [],
        "part2": data.part2 or [],
        "part3": data.part3 or [],
        "part4": data.part4 or [],
        "part5": data.part5 or [],
        "part6": data.part6 or [],
    }
    correct_parts = {
        "part1": answer_obj.part_1 or [],
        "part2": answer_obj.part_2 or [],
        "part3": answer_obj.part_3 or [],
        "part4": answer_obj.part_4 or [],
        "part5": answer_obj.part_5 or [],
        "part6": answer_obj.part_6 or [],
    }

    part_scores = {
        "part1": {"correct": 0, "total": len(correct_parts["part1"])},
        "part2": {"correct": 0, "total": len(correct_parts["part2"])},
        "part3": {"correct": 0, "total": len(correct_parts["part3"])},
        "part4": {"correct": 0, "total": len(correct_parts["part4"])},
        "part5": {"correct": 0, "total": len(correct_parts["part5"])},
        "part6": {"correct": 0, "total": len(correct_parts["part6"])},
    }

    details = []
    total = 0
    question_no = 1
    ordered_parts = ["part1", "part2", "part3", "part4", "part5", "part6"]
    for part_name in ordered_parts:
        for idx, correct_value in enumerate(correct_parts[part_name]):
            user_value = user_parts[part_name][idx] if idx < len(user_parts[part_name]) else ""
            is_correct = normalize(user_value) == normalize(correct_value)
            if is_correct:
                total += 1
                part_scores[part_name]["correct"] += 1
            details.append(
                {
                    "question": question_no,
                    "part": int(part_name.replace("part", "")),
                    "user_answer": user_value,
                    "correct_answer": correct_value,
                    "is_correct": is_correct,
                }
            )
            question_no += 1

    max_score = sum(x["total"] for x in part_scores.values())
    percentage = round((total / max_score) * 100) if max_score > 0 else 0

    results = {
        "total": total,
        "maxScore": max_score,
        "percentage": percentage,
        "details": details,
        "partScores": part_scores,
    }

    # Telegram archive (non-audio: HTML)
    try:
        submitted_at = datetime.utcnow().isoformat()
        html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CEFR Listening Submission</title>
</head>
<body>
  <h2>CEFR Listening Submission</h2>
  <p><strong>User ID:</strong> {current_user.id}</p>
  <p><strong>Username:</strong> {escape(current_user.username or "-")}</p>
  <p><strong>Email:</strong> {escape(current_user.email or "-")}</p>
  <p><strong>Mock ID:</strong> {data.mock_id}</p>
  <p><strong>Submitted At:</strong> {submitted_at}</p>
  <hr />
  <h3>Score Summary</h3>
  <pre>{escape(json.dumps(results, ensure_ascii=False, indent=2))}</pre>
  <h3>User Answers</h3>
  <pre>{escape(json.dumps(user_parts, ensure_ascii=False, indent=2))}</pre>
  <h3>Correct Answers Snapshot</h3>
  <pre>{escape(json.dumps(correct_parts, ensure_ascii=False, indent=2))}</pre>
</body>
</html>"""

        caption = (
            f"CEFR Listening submission\n"
            f"User: {current_user.id}\n"
            f"Mock: {data.mock_id}\n"
            f"Total: {total}/{max_score}"
        )
        send_document_to_telegram(
            file_buffer=io.BytesIO(html_doc.encode("utf-8")),
            filename=f"cefr_listening_user{current_user.id}_mock{data.mock_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html",
            caption=caption,
            mime_type="text/html",
            chat_id=os.getenv("LISTENING_ARCHIVE_CHANNEL"),
        )
    except Exception as e:
        print(f"Listening telegram archive error: {e}")

    return results
