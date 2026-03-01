from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db, ReadingMockAnswer, ReadingMockQuestion
from auth.auth import verify_role, get_current_user
from schemas.ReadingMockQuestionSchema import CreateReadingMock, CreateReadingAnswers, UpdateReadingAnswers, Results
from services.telegram_bot import send_document_to_telegram
from datetime import datetime
from html import escape
import io
import os

router = APIRouter(prefix="/mock/reading")

# -------------------------
# Reading Mock Questions CRUD
# -------------------------

@router.get("/all")
def get_all_reading_mocks(db: Session = Depends(get_db)):
    mocks = db.query(ReadingMockQuestion).all()
    return {"mocks": mocks}


@router.get("/mock/{id}")
def get_mock(id: int, db: Session = Depends(get_db)):
    mock = db.query(ReadingMockQuestion).filter(ReadingMockQuestion.id == id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found.")
    return {"mock": mock}


@router.post("/")
def create_mock(
    data: CreateReadingMock, 
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    new_mock = ReadingMockQuestion(
        title=data.title,
        part1=data.part1,
        part2=data.part2,
        part3=data.part3,
        part4=data.part4,
        part5=data.part5,
    )
    db.add(new_mock)
    db.commit()
    db.refresh(new_mock)
    return {"message": "Mock created successfully.", "mock_id": new_mock.id}


@router.put("/{id}")
def update_mock(
    id: int,
    data: CreateReadingMock,
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    mock = db.query(ReadingMockQuestion).filter(ReadingMockQuestion.id == id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found.")

    mock.title = data.title
    mock.part1 = data.part1
    mock.part2 = data.part2
    mock.part3 = data.part3
    mock.part4 = data.part4
    mock.part5 = data.part5

    db.commit()
    db.refresh(mock)
    return {"message": "Mock updated successfully."}


@router.delete("/{id}")
def delete_mock(
    id: int,
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    mock = db.query(ReadingMockQuestion).filter(ReadingMockQuestion.id == id).first()
    if not mock:
        raise HTTPException(status_code=404, detail="Mock not found.")

    db.delete(mock)
    db.commit()
    return {"message": "Mock deleted successfully."}


# -------------------------
# Answers CRUD
# -------------------------

@router.get("/answers")
def get_answers(
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    answers = db.query(ReadingMockAnswer).all()
    return {"answers": answers}


@router.get("/answer/{q_id}")
def get_answer(
    q_id: int,
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    answer = db.query(ReadingMockAnswer).filter(ReadingMockAnswer.question_id == q_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answers not found.")
    return {"answers": answer}


@router.post("/answer")
def add_answers(
    data: CreateReadingAnswers,
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    existing = db.query(ReadingMockAnswer).filter(ReadingMockAnswer.question_id == data.question_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Answers already exist for this question.")

    new_answer = ReadingMockAnswer(
        part1=data.part1,
        part2=data.part2,
        part3=data.part3,
        part4=data.part4,
        part5=data.part5,
        question_id=data.question_id
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return {"message": "Answers created successfully.", "answer_id": new_answer.id}


@router.put("/answer/{id}")
def update_answers(
    id: int,
    data: UpdateReadingAnswers,
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    answer = db.query(ReadingMockAnswer).filter(ReadingMockAnswer.id == id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found.")

    answer.part1 = data.part1
    answer.part2 = data.part2
    answer.part3 = data.part3
    answer.part4 = data.part4
    answer.part5 = data.part5

    db.commit()
    db.refresh(answer)
    return {"message": "Answers updated successfully."}


@router.delete("/answer/{id}")
def delete_answers(
    id: int, 
    db: Session = Depends(get_db),
    user = Depends(verify_role(["admin"]))
):
    answer = db.query(ReadingMockAnswer).filter(ReadingMockAnswer.id == id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found.")

    db.delete(answer)
    db.commit()
    return {"message": "Answer deleted successfully."}

@router.post("/submit")
def check_mock(
    data: Results,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Check user answers against correct answers
    
    Part 1: 6 gaps - tekshirish case-insensitive
    Part 2: 10 matching answers - tekshirish case-insensitive (raqam yoki harf)
    Part 3: 6 heading answers - tekshirish case-insensitive (raqam yoki harf)
    Part 4 MC: 4 questions - tekshirish case-insensitive (A/B/C/D)
    Part 4 TF: 5 statements - tekshirish case-insensitive (True/False/Not Given)
    Part 5 Mini: 5 gaps - tekshirish case-insensitive
    Part 5 MC: 2 questions - tekshirish case-insensitive (A/B/C/D)
    """
    
    # Question mavjudligini tekshir
    question = db.query(ReadingMockQuestion).filter(
        ReadingMockQuestion.id == data.question_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Question not found."
        )
    
    # Javoblarni olish
    answer_obj = question.answers
    
    if not answer_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Answers not found."
        )
    
    # Natijalar dictionary
    results = {
        "part1": 0,
        "part2": 0,
        "part3": 0,
        "part4MC": 0,
        "part4TF": 0,
        "part5Mini": 0,
        "part5MC": 0,
        "total": 0
    }
    
    def normalize(value):
        if value is None:
            return ""
        return str(value).strip()

    answer_part1 = answer_obj.part1 or []
    answer_part2 = answer_obj.part2 or []
    answer_part3 = answer_obj.part3 or []
    answer_part4 = answer_obj.part4 or []
    answer_part5 = answer_obj.part5 or []

    # Legacy DB format:
    # part4 = [4x MC, 5x TF] and part5 = [5x Mini, 2x MC]
    correct_part4_mc = answer_part4[:4]
    correct_part4_tf = answer_part4[4:9]
    correct_part5_mini = answer_part5[:5]
    correct_part5_mc = answer_part5[5:7]

    # ============ PART 1 TEKSHIRISH ============
    # 6 ta bo'shliq - so'z yoki raqam
    try:
        for i, user_ans in enumerate(data.part1):
            if i < len(answer_part1):
                correct_ans = normalize(answer_part1[i]).lower()
                user_answer = normalize(user_ans).lower()
                if correct_ans == user_answer:
                    results["part1"] += 1
    except Exception as e:
        print(f"Part 1 error: {e}")
    
    # ============ PART 2 TEKSHIRISH ============
    # 10 ta matching - raqam yoki harf (1-7 orasida)
    try:
        for i, user_ans in enumerate(data.part2):
            if i < len(answer_part2):
                correct_ans = normalize(answer_part2[i]).lower()
                user_answer = normalize(user_ans).lower()
                if correct_ans == user_answer:
                    results["part2"] += 1
    except Exception as e:
        print(f"Part 2 error: {e}")
    
    # ============ PART 3 TEKSHIRISH ============
    # 6 ta paragraf - sarlavha raqami (1-8 orasida)
    try:
        for i, user_ans in enumerate(data.part3):
            if i < len(answer_part3):
                correct_ans = normalize(answer_part3[i]).lower()
                user_answer = normalize(user_ans).lower()
                if correct_ans == user_answer:
                    results["part3"] += 1
    except Exception as e:
        print(f"Part 3 error: {e}")
    
    # ============ PART 4 MC TEKSHIRISH ============
    # 4 ta test savol - A/B/C/D
    try:
        for i, user_ans in enumerate(data.part4MC):
            if i < len(correct_part4_mc):
                correct_ans = normalize(correct_part4_mc[i]).upper()
                user_answer = normalize(user_ans).upper()
                if correct_ans == user_answer:
                    results["part4MC"] += 1
    except Exception as e:
        print(f"Part 4 MC error: {e}")
    
    # ============ PART 4 TRUE/FALSE/NOT GIVEN TEKSHIRISH ============
    # 5 ta statement - True/False/Not Given
    try:
        for i, user_ans in enumerate(data.part4TF):
            if i < len(correct_part4_tf):
                correct_ans = normalize(correct_part4_tf[i]).lower()
                user_answer = normalize(user_ans).lower()
                if correct_ans == user_answer:
                    results["part4TF"] += 1
    except Exception as e:
        print(f"Part 4 TF error: {e}")
    
    # ============ PART 5 MINI TEXT TEKSHIRISH ============
    # 5 ta bo'shliq - so'z yoki raqam
    try:
        for i, user_ans in enumerate(data.part5Mini):
            if i < len(correct_part5_mini):
                correct_ans = normalize(correct_part5_mini[i]).lower()
                user_answer = normalize(user_ans).lower()
                if correct_ans == user_answer:
                    results["part5Mini"] += 1
    except Exception as e:
        print(f"Part 5 Mini error: {e}")
    
    # ============ PART 5 MC TEKSHIRISH ============
    # 2 ta test savol - A/B/C/D
    try:
        for i, user_ans in enumerate(data.part5MC):
            if i < len(correct_part5_mc):
                correct_ans = normalize(correct_part5_mc[i]).upper()
                user_answer = normalize(user_ans).upper()
                if correct_ans == user_answer:
                    results["part5MC"] += 1
    except Exception as e:
        print(f"Part 5 MC error: {e}")
    
    # ============ UMUMIY NATIJA ============
    results["total"] = (
        results["part1"] + 
        results["part2"] + 
        results["part3"] + 
        results["part4MC"] + 
        results["part4TF"] + 
        results["part5Mini"] + 
        results["part5MC"]
    )

    # Telegram archive (non-audio: HTML)
    try:
        submitted_label = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        part1_text = (question.part1 or {}).get("text", "")
        part2_statements = (question.part2 or {}).get("statements", []) or []
        part3_paragraphs = (question.part3 or {}).get("paragraphs", []) or []
        part4_mc = (question.part4 or {}).get("multipleChoice", []) or []
        part4_tf = (question.part4 or {}).get("trueFalse", []) or []
        part5_mc = (question.part5 or {}).get("multipleChoice", []) or []

        def render_qa_card(q_no, section, prompt, user_answer, correct_answer, is_correct):
            status_class = "ok" if is_correct else "bad"
            status_text = "Correct" if is_correct else "Incorrect"
            return f"""
<div class="qa-card {status_class}">
  <div class="qa-head">
    <span class="qno">Q{q_no}</span>
    <span class="sec">{escape(section)}</span>
    <span class="st">{status_text}</span>
  </div>
  <div class="qa-body">
    <div class="label">Question</div>
    <p class="prompt">{escape(str(prompt or "-"))}</p>
    <div class="row"><b>User:</b> {escape(str(user_answer if user_answer is not None else ""))}</div>
    <div class="row"><b>Correct:</b> {escape(str(correct_answer if correct_answer is not None else ""))}</div>
  </div>
</div>"""

        cards = []
        q_no = 1

        for idx, ua in enumerate(data.part1 or []):
            ca = answer_part1[idx] if idx < len(answer_part1) else ""
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 1",
                prompt=f"Gap {idx + 1} from Part 1 text: {part1_text}",
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().lower() == str(ca).strip().lower(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part2 or []):
            ca = answer_part2[idx] if idx < len(answer_part2) else ""
            prompt = part2_statements[idx] if idx < len(part2_statements) else f"Part 2 statement {idx + 1}"
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 2",
                prompt=prompt,
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().lower() == str(ca).strip().lower(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part3 or []):
            ca = answer_part3[idx] if idx < len(answer_part3) else ""
            prompt = part3_paragraphs[idx] if idx < len(part3_paragraphs) else f"Part 3 paragraph {idx + 1}"
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 3",
                prompt=prompt,
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().lower() == str(ca).strip().lower(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part4MC or []):
            ca = correct_part4_mc[idx] if idx < len(correct_part4_mc) else ""
            mc_q = part4_mc[idx] if idx < len(part4_mc) else {}
            prompt = mc_q.get("question") if isinstance(mc_q, dict) else f"Part 4 MC question {idx + 1}"
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 4 MC",
                prompt=prompt,
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().upper() == str(ca).strip().upper(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part4TF or []):
            ca = correct_part4_tf[idx] if idx < len(correct_part4_tf) else ""
            tf_q = part4_tf[idx] if idx < len(part4_tf) else {}
            prompt = tf_q.get("statement") if isinstance(tf_q, dict) else f"Part 4 TF statement {idx + 1}"
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 4 TF",
                prompt=prompt,
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().lower() == str(ca).strip().lower(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part5Mini or []):
            ca = correct_part5_mini[idx] if idx < len(correct_part5_mini) else ""
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 5 Mini",
                prompt=f"Gap {idx + 1} from Part 5 mini text",
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().lower() == str(ca).strip().lower(),
            ))
            q_no += 1

        for idx, ua in enumerate(data.part5MC or []):
            ca = correct_part5_mc[idx] if idx < len(correct_part5_mc) else ""
            mc_q = part5_mc[idx] if idx < len(part5_mc) else {}
            prompt = mc_q.get("question") if isinstance(mc_q, dict) else f"Part 5 MC question {idx + 1}"
            cards.append(render_qa_card(
                q_no=q_no,
                section="Part 5 MC",
                prompt=prompt,
                user_answer=ua,
                correct_answer=ca,
                is_correct=str(ua).strip().upper() == str(ca).strip().upper(),
            ))
            q_no += 1

        cards_html = "\n".join(cards)
        html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CEFR Reading Submission</title>
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
      <h1>CEFR Reading Archive</h1>
      <div class="meta">
        <div><b>Mock ID:</b> {data.question_id}</div>
        <div><b>Submitted:</b> {submitted_label}</div>
        <div><b>Total:</b> {results["total"]}/38</div>
        <div><b>User ID:</b> {current_user.id}</div>
        <div><b>Username:</b> {escape(current_user.username or "-")}</div>
        <div><b>Email:</b> {escape(current_user.email or "-")}</div>
      </div>
    </div>
    <div class="summary">
      <span class="chip">Part1: {results["part1"]}/6</span>
      <span class="chip">Part2: {results["part2"]}/10</span>
      <span class="chip">Part3: {results["part3"]}/6</span>
      <span class="chip">Part4 MC: {results["part4MC"]}/4</span>
      <span class="chip">Part4 TF: {results["part4TF"]}/5</span>
      <span class="chip">Part5 Mini: {results["part5Mini"]}/5</span>
      <span class="chip">Part5 MC: {results["part5MC"]}/2</span>
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
            f"📖 CEFR Reading Archive\n"
            f"👤 User ID: {current_user.id}\n"
            f"📘 Mock ID: {data.question_id}\n"
            f"📊 Score: {results['total']}/38\n"
            f"⏰ Submitted: {submitted_label}"
        )
        send_document_to_telegram(
            file_buffer=io.BytesIO(html_doc.encode("utf-8")),
            filename=f"cefr_reading_user{current_user.id}_question{data.question_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html",
            caption=caption,
            mime_type="text/html",
            chat_id=os.getenv("READING_ARCHIVE_CHANNEL"),
        )
    except Exception as e:
        print(f"Reading telegram archive error: {e}")

    return results
