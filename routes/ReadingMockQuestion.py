from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db, User, ReadingMockAnswer, ReadingMockQuestion, Submissions
from auth.auth import verify_role
from schemas.ReadingMockQuestionSchema import CreateReadingMock, CreateReadingAnswers, UpdateReadingAnswers, Results

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
def check_mock(data: Results, db: Session = Depends(get_db)):
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
    
    # ============ PART 1 TEKSHIRISH ============
    # 6 ta bo'shliq - so'z yoki raqam
    try:
        for i, user_ans in enumerate(data.part1):
            if i < len(answer_obj.part1):
                correct_ans = answer_obj.part1[i].strip().lower()
                user_answer = user_ans.strip().lower()
                if correct_ans == user_answer:
                    results["part1"] += 1
    except Exception as e:
        print(f"Part 1 error: {e}")
    
    # ============ PART 2 TEKSHIRISH ============
    # 10 ta matching - raqam yoki harf (1-7 orasida)
    try:
        for i, user_ans in enumerate(data.part2):
            if i < len(answer_obj.part2):
                correct_ans = answer_obj.part2[i].strip().lower()
                user_answer = user_ans.strip().lower()
                if correct_ans == user_answer:
                    results["part2"] += 1
    except Exception as e:
        print(f"Part 2 error: {e}")
    
    # ============ PART 3 TEKSHIRISH ============
    # 6 ta paragraf - sarlavha raqami (1-8 orasida)
    try:
        for i, user_ans in enumerate(data.part3):
            if i < len(answer_obj.part3):
                correct_ans = answer_obj.part3[i].strip().lower()
                user_answer = user_ans.strip().lower()
                if correct_ans == user_answer:
                    results["part3"] += 1
    except Exception as e:
        print(f"Part 3 error: {e}")
    
    # ============ PART 4 MC TEKSHIRISH ============
    # 4 ta test savol - A/B/C/D
    try:
        for i, user_ans in enumerate(data.part4MC):
            if i < len(answer_obj.part4MC):
                correct_ans = answer_obj.part4MC[i].strip().upper()
                user_answer = user_ans.strip().upper()
                if correct_ans == user_answer:
                    results["part4MC"] += 1
    except Exception as e:
        print(f"Part 4 MC error: {e}")
    
    # ============ PART 4 TRUE/FALSE/NOT GIVEN TEKSHIRISH ============
    # 5 ta statement - True/False/Not Given
    try:
        for i, user_ans in enumerate(data.part4TF):
            if i < len(answer_obj.part4TF):
                correct_ans = answer_obj.part4TF[i].strip().lower()
                user_answer = user_ans.strip().lower()
                if correct_ans == user_answer:
                    results["part4TF"] += 1
    except Exception as e:
        print(f"Part 4 TF error: {e}")
    
    # ============ PART 5 MINI TEXT TEKSHIRISH ============
    # 5 ta bo'shliq - so'z yoki raqam
    try:
        for i, user_ans in enumerate(data.part5Mini):
            if i < len(answer_obj.part5Mini):
                correct_ans = answer_obj.part5Mini[i].strip().lower()
                user_answer = user_ans.strip().lower()
                if correct_ans == user_answer:
                    results["part5Mini"] += 1
    except Exception as e:
        print(f"Part 5 Mini error: {e}")
    
    # ============ PART 5 MC TEKSHIRISH ============
    # 2 ta test savol - A/B/C/D
    try:
        for i, user_ans in enumerate(data.part5MC):
            if i < len(answer_obj.part5MC):
                correct_ans = answer_obj.part5MC[i].strip().upper()
                user_answer = user_ans.strip().upper()
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
    userInfo = User.filter(User.id == user.id).first()
    submission = Submissions(username = userInfo.username, section = 'CEFR Reading',score=results["total"])
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return results
