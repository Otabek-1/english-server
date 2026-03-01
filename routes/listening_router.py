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
        submitted_label = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        part_data = mock.data or {}
        prompts = []

        for idx, options in enumerate(part_data.get("part_1", []) or []):
            if isinstance(options, list):
                opts = ", ".join([f"{chr(65 + i)}. {str(opt)}" for i, opt in enumerate(options)])
                prompts.append(f"Part 1 - Question {idx + 1}: {opts}")
            else:
                prompts.append(f"Part 1 - Question {idx + 1}")

        for idx, item in enumerate(part_data.get("part_2", []) or []):
            if isinstance(item, dict):
                prompt_text = f"{item.get('label', '').strip()} {item.get('before', '').strip()} ____ {item.get('after', '').strip()}".strip()
                prompts.append(f"Part 2 - Question {idx + 1}: {prompt_text}")
            else:
                prompts.append(f"Part 2 - Question {idx + 1}")

        for idx, speaker in enumerate((part_data.get("part_3", {}) or {}).get("speakers", []) or []):
            prompts.append(f"Part 3 - Speaker {idx + 1}: {speaker}")

        for idx, q in enumerate((part_data.get("part_4", {}) or {}).get("questions", []) or []):
            if isinstance(q, dict):
                prompts.append(f"Part 4 - Map label {idx + 1}: {q.get('place', '')}")
            else:
                prompts.append(f"Part 4 - Question {idx + 1}")

        for extract in part_data.get("part_5", []) or []:
            extract_name = extract.get("name", "Extract") if isinstance(extract, dict) else "Extract"
            qs = extract.get("questions", []) if isinstance(extract, dict) else []
            for q in qs:
                if isinstance(q, dict):
                    prompts.append(f"Part 5 - {extract_name}: {q.get('text', '')}")
                else:
                    prompts.append(f"Part 5 - {extract_name}")

        for idx, q in enumerate((part_data.get("part_6", {}) or {}).get("questions", []) or []):
            if isinstance(q, dict):
                prompt_text = q.get("text") or q.get("question") or q.get("before") or f"Question {idx + 1}"
            else:
                prompt_text = str(q)
            prompts.append(f"Part 6 - Question {idx + 1}: {prompt_text}")

        def render_detail_card(detail, prompt, idx):
            status_class = "ok" if detail.get("is_correct") else "bad"
            status_text = "Correct" if detail.get("is_correct") else "Incorrect"
            return f"""
<div class="qa-card {status_class}">
  <div class="qa-head">
    <span class="qno">Q{detail.get('question', idx + 1)}</span>
    <span class="sec">Part {detail.get('part', '-')}</span>
    <span class="st">{status_text}</span>
  </div>
  <div class="qa-body">
    <div class="label">Question</div>
    <p class="prompt">{escape(str(prompt or "-"))}</p>
    <div class="row"><b>User:</b> {escape(str(detail.get("user_answer", "")))}</div>
    <div class="row"><b>Correct:</b> {escape(str(detail.get("correct_answer", "")))}</div>
  </div>
</div>"""

        cards_html = "\n".join(
            render_detail_card(detail, prompts[idx] if idx < len(prompts) else f"Question {idx + 1}", idx)
            for idx, detail in enumerate(details)
        )
        html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CEFR Listening Submission</title>
  <style>
    :root {{
      --bg: #f4f7fb; --card:#fff; --ink:#102238; --muted:#5c6b80; --line:#d7e0ec;
      --primary:#0f766e; --primary2:#0891b2; --ok:#1f9d55; --bad:#cc3344;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; padding:28px; background:linear-gradient(180deg,#edf7f9,var(--bg)); color:var(--ink); font-family:Segoe UI,Arial,sans-serif; }}
    .wrap {{ max-width:1100px; margin:0 auto; background:var(--card); border:1px solid var(--line); border-radius:18px; overflow:hidden; box-shadow:0 14px 34px rgba(16,34,56,.12); }}
    .hero {{ padding:24px 28px; background:linear-gradient(120deg,var(--primary),var(--primary2)); color:#fff; }}
    .hero h1 {{ margin:0 0 8px; font-size:30px; }}
    .meta {{ display:grid; grid-template-columns:repeat(3,minmax(180px,1fr)); gap:8px 16px; font-size:14px; }}
    .summary {{ padding:16px 28px; border-bottom:1px solid var(--line); display:flex; gap:16px; flex-wrap:wrap; }}
    .chip {{ background:#eef6ff; border:1px solid #cfe0ff; color:#123a78; border-radius:999px; padding:6px 12px; font-size:13px; font-weight:700; }}
    .body {{ padding:20px 28px 28px; }}
    .qa-grid {{ display:grid; grid-template-columns:1fr; gap:12px; }}
    .qa-card {{ border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }}
    .qa-card.ok {{ border-left:6px solid var(--ok); }}
    .qa-card.bad {{ border-left:6px solid var(--bad); }}
    .qa-head {{ display:flex; gap:8px; align-items:center; padding:10px 12px; background:#f8fbff; border-bottom:1px solid var(--line); }}
    .qno {{ font-weight:800; color:#0a4f8a; }}
    .sec {{ font-size:12px; font-weight:700; color:#19436b; background:#e8f1ff; border-radius:999px; padding:4px 8px; }}
    .st {{ margin-left:auto; font-size:12px; font-weight:700; color:#4a5b70; }}
    .qa-body {{ padding:12px; }}
    .label {{ font-size:11px; text-transform:uppercase; color:#375273; font-weight:700; letter-spacing:.04em; margin-bottom:6px; }}
    .prompt {{ margin:0 0 10px; white-space:pre-wrap; color:#1f3653; }}
    .row {{ font-size:14px; margin:3px 0; }}
    @media (max-width:820px) {{ body {{ padding:14px; }} .meta {{ grid-template-columns:1fr 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>CEFR Listening Archive</h1>
      <div class="meta">
        <div><b>Mock ID:</b> {data.mock_id}</div>
        <div><b>Submitted:</b> {submitted_label}</div>
        <div><b>Total:</b> {total}/{max_score}</div>
        <div><b>User ID:</b> {current_user.id}</div>
        <div><b>Username:</b> {escape(current_user.username or "-")}</div>
        <div><b>Email:</b> {escape(current_user.email or "-")}</div>
      </div>
    </div>
    <div class="summary">
      <span class="chip">Part1: {part_scores["part1"]["correct"]}/{part_scores["part1"]["total"]}</span>
      <span class="chip">Part2: {part_scores["part2"]["correct"]}/{part_scores["part2"]["total"]}</span>
      <span class="chip">Part3: {part_scores["part3"]["correct"]}/{part_scores["part3"]["total"]}</span>
      <span class="chip">Part4: {part_scores["part4"]["correct"]}/{part_scores["part4"]["total"]}</span>
      <span class="chip">Part5: {part_scores["part5"]["correct"]}/{part_scores["part5"]["total"]}</span>
      <span class="chip">Part6: {part_scores["part6"]["correct"]}/{part_scores["part6"]["total"]}</span>
      <span class="chip">Percent: {percentage}%</span>
    </div>
    <div class="body">
      <div class="qa-grid">
        {cards_html}
      </div>
    </div>
  </div>
</body>
</html>"""

        caption = (
            f"🎧 CEFR Listening Archive\n"
            f"👤 User ID: {current_user.id}\n"
            f"📘 Mock ID: {data.mock_id}\n"
            f"📊 Score: {total}/{max_score} ({percentage}%)\n"
            f"⏰ Submitted: {submitted_label}"
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
