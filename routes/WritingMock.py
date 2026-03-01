from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user
from database.db import get_db, WritingMock, WritingResult, User
from schemas.WritingMockSchema import CreateMockData, MockResponse, Result
from services.email_service import send_email
from services.telegram_bot import send_document_to_telegram
from datetime import datetime
from html import escape
import io
import os

router = APIRouter(prefix="/mock/writing", tags=["Writing", "Mock","CEFR"])

@router.get("/all")
def get_all_writings(db: Session = Depends(get_db)):
    data = db.query(WritingMock).all()
    return data

@router.get("/mock/{id}")
def get_by_id(id:int, db: Session = Depends(get_db)):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return exists

@router.post("/create")
def create_mock(data:CreateMockData, db: Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    mock = WritingMock(images=data.images,task1=data.task1,task2=data.task2)
    db.add(mock)
    db.commit()
    db.refresh(mock)
    return {"message":"Mock created successfully.", "mock":mock}

@router.put("/update/{id}")
def update_mock(id: int, data:CreateMockData,db:Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    exists.images = data.images
    exists.task1 = data.task1
    exists.task2 = data.task2
    db.commit()
    db.refresh(exists)
    return {"message":"Updated successfully."}

@router.delete("/delete/{id}")
def delete_mock(id:int, db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    exists = db.query(WritingMock).filter(WritingMock.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    db.delete(exists)
    db.commit()
    return {"message":"Deleted successfully."}

@router.post("/submit")
def submit_mock(data: MockResponse,db:Session = Depends(get_db), user = Depends(get_current_user)):
    mock = db.query(WritingMock).filter(WritingMock.id == data.mock_id).first()
    if not mock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock not found.")

    result = WritingResult(user_id = user.id, task1= data.task1, task2=data.task2,mock_id=data.mock_id)
    db.add(result)
    db.commit()
    db.refresh(result)

    # Archive raw submission to Telegram as HTML document
    try:
        task_11 = data.task1
        task_12 = ""
        if " ---TASK--- " in data.task1:
            task_11, task_12 = data.task1.split(" ---TASK--- ", 1)

        created_at = result.created_at or datetime.utcnow()
        task11_prompt = ((mock.task1 or {}).get("task11") or "").strip()
        task12_prompt = ((mock.task1 or {}).get("task12") or "").strip()
        task2_prompt = ((mock.task2 or {}).get("task2") or "").strip()
        created_at_label = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CEFR Writing Submission</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --card: #ffffff;
      --ink: #102238;
      --muted: #5c6b80;
      --line: #d7e0ec;
      --primary: #0d6efd;
      --primary-2: #4f46e5;
      --ok-bg: #e8f7ef;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px;
      background: linear-gradient(180deg, #eef3fa 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: Segoe UI, Arial, sans-serif;
      line-height: 1.45;
    }}
    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 14px 34px rgba(16, 34, 56, 0.12);
    }}
    .hero {{
      padding: 24px 28px;
      background: linear-gradient(120deg, var(--primary), var(--primary-2));
      color: #fff;
    }}
    .hero h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(3, minmax(180px, 1fr));
      gap: 8px 16px;
      margin-top: 8px;
      font-size: 14px;
    }}
    .meta b {{ opacity: .85; font-weight: 600; }}
    .body {{ padding: 24px 28px 28px; }}
    .task {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
      background: #fff;
    }}
    .task h2 {{ margin: 0 0 10px; font-size: 22px; }}
    .label {{
      font-size: 12px;
      font-weight: 700;
      color: #0b4db6;
      background: #e8f0ff;
      display: inline-block;
      padding: 5px 9px;
      border-radius: 999px;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    .prompt {{
      margin: 0 0 10px;
      padding: 11px 12px;
      border-radius: 10px;
      border: 1px solid #dbe7ff;
      background: #f4f8ff;
      color: #1e3554;
      white-space: pre-wrap;
    }}
    .answer {{
      margin: 0;
      padding: 12px;
      border-radius: 10px;
      background: #f7fafc;
      border: 1px solid var(--line);
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 14px;
    }}
    .footer {{
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
      text-align: right;
    }}
    @media (max-width: 820px) {{
      body {{ padding: 14px; }}
      .meta {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>CEFR Writing Archive</h1>
      <div class="meta">
        <div><b>Mock ID:</b> {data.mock_id}</div>
        <div><b>Result ID:</b> {result.id}</div>
        <div><b>Submitted:</b> {created_at_label}</div>
        <div><b>User ID:</b> {user.id}</div>
        <div><b>Username:</b> {escape(user.username or "-")}</div>
        <div><b>Email:</b> {escape(user.email or "-")}</div>
      </div>
    </div>
    <div class="body">
      <section class="task">
        <h2>Task 1.1</h2>
        <div class="label">Question Prompt</div>
        <p class="prompt">{escape(task11_prompt or "Task prompt not found")}</p>
        <div class="label">User Answer</div>
        <pre class="answer">{escape(task_11 or "")}</pre>
      </section>
      <section class="task">
        <h2>Task 1.2</h2>
        <div class="label">Question Prompt</div>
        <p class="prompt">{escape(task12_prompt or "Task prompt not found")}</p>
        <div class="label">User Answer</div>
        <pre class="answer">{escape(task_12 or "")}</pre>
      </section>
      <section class="task">
        <h2>Task 2</h2>
        <div class="label">Question Prompt</div>
        <p class="prompt">{escape(task2_prompt or "Task prompt not found")}</p>
        <div class="label">User Answer</div>
        <pre class="answer">{escape(data.task2 or "")}</pre>
      </section>
      <div class="footer">Generated by Mockstream Telegram Archive</div>
    </div>
  </div>
</body>
</html>"""

        caption = (
            f"📝 CEFR Writing Archive\n"
            f"👤 User ID: {user.id}\n"
            f"📘 Mock ID: {data.mock_id}\n"
            f"🧾 Result ID: {result.id}\n"
            f"⏰ Submitted: {created_at_label}"
        )
        send_document_to_telegram(
            file_buffer=io.BytesIO(html_doc.encode("utf-8")),
            filename=f"cefr_writing_user{user.id}_mock{data.mock_id}_result{result.id}.html",
            caption=caption,
            mime_type="text/html",
            chat_id=os.getenv("WRITING_ARCHIVE_CHANNEL"),
        )
    except Exception as e:
        print(f"Writing telegram archive error: {e}")

    return {"message":"Accepted successfully."}

@router.get("/results")
def get_all_results(db: Session = Depends(get_db), user = Depends(verify_role(["admin"]))):
    res = db.query(WritingResult).all()
    return res

@router.get("/result/{id}")
def get_result_by_id(id:int, db:Session = Depends(get_db), user = Depends(get_current_user)):
    exists = db.query(WritingResult).filter(WritingResult.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return {"mock":exists}

@router.post("/check/{id}")
def check_result(id:int,data:Result, db:Session = Depends(get_db), user = Depends(verify_role(['admin']))):
    exists = db.query(WritingResult).filter(WritingResult.id == id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    result_data = {"scores":data.result["scores"],"band":data.result["band"],"feedbacks":data.result["feedbacks"],"submitted_at":data.result["submitted_at"]}
    if data.result["send_email"]:
        user = db.query(User).filter(User.id == data.result["user_id"]).first()
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
        border-bottom: 3px solid #e74c3c;
        padding-bottom: 20px;
        margin-bottom: 30px;
      }}
      .header h1 {{
        color: #e74c3c;
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
        border-left: 4px solid #e74c3c;
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
        color: #e74c3c;
        font-weight: bold;
        font-size: 16px;
      }}
      .band-display {{
        text-align: center;
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        padding: 20px;
        border-radius: 5px;
        margin: 20px 0;
        font-size: 32px;
        font-weight: bold;
      }}
      .task-section {{
        background-color: #f9f9f9;
        padding: 15px;
        margin: 15px 0;
        border-radius: 5px;
        border-left: 4px solid #3498db;
      }}
      .task-title {{
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 8px;
        font-size: 16px;
      }}
      .task-score {{
        display: inline-block;
        background-color: #3498db;
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
      .submitted-time {{
        color: #7f8c8d;
        font-size: 12px;
        margin-top: 10px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>📝 Writing Mock Review</h1>
        <p>Your assessment results are ready</p>
      </div>

      <div class="score-box">
        <div class="score-row">
          <span class="score-label">Mock ID:</span>
          <span>{data.result["mock_id"]}</span>
        </div>
        <div class="score-row">
          <span class="score-label">Total Score:</span>
          <span class="score-value">{data.result["scores"]["total"]}/17</span>
        </div>
      </div>

      <div class="band-display">
        {data.result["band"]}
      </div>

      <div class="task-section">
        <div class="task-title">✓ Task 1.1</div>
        <div class="task-score">Score: {data.result["scores"]["task11"]}/5</div>
        <div class="feedback-text">
          {data.result["feedbacks"]["task11"]}
        </div>
      </div>

      <div class="task-section">
        <div class="task-title">✓ Task 1.2</div>
        <div class="task-score">Score: {data.result["scores"]["task12"]}/6</div>
        <div class="feedback-text">
          {data.result["feedbacks"]["task12"]}
        </div>
      </div>

      <div class="task-section">
        <div class="task-title">✓ Task 2</div>
        <div class="task-score">Score: {data.result["scores"]["task2"]}/6</div>
        <div class="feedback-text">
          {data.result["feedbacks"]["task2"]}
        </div>
      </div>

      <div class="footer">
        <p>Thank you for taking the Writing Mock test!</p>
        <div class="submitted-time">
          Submitted: {data.result["submitted_at"]}
        </div>
        <p style="margin-top: 15px; color: #bdc3c7;">
          © 2025 MockStream & CodeCraft;
        </p>
      </div>
    </div>
  </body>
</html>
"""
        send_email(user.email, f"Writing mock #{data.result['mock_id']} results", message)
    exists.result = result_data
    db.commit()
    db.refresh(exists)
    return {"message":"Checked successfully.","data":data}
