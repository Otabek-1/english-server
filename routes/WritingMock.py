from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from auth.auth import verify_role, get_current_user
from database.db import get_db, WritingMock, WritingResult, User
from schemas.WritingMockSchema import CreateMockData, MockResponse, Result
from services.email_service import send_email

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
    result = WritingResult(user_id = user.id, task1= data.task1, task2=data.task2,mock_id=data.mock_id)
    db.add(result)
    db.commit()
    db.refresh(result)
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
        send_email(user.email,f"Writing mock #{data.result["mock_id"]} results",message)
    exists.result = result_data
    db.commit()
    db.refresh(exists)
    return {"message":"Checked successfully.","data":data}
