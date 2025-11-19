from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db, User, ReadingMockAnswer, ReadingMockQuestion
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
def check_mock(data:Results, db:Session = Depends(get_db)):
    exists = db.query(ReadingMockQuestion).filter(ReadingMockQuestion.id == data.question_id).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answers not found.")
    answers = exists.answers
    results = dict()
    results["part1"] = 0
    results["part2"] = 0
    results["part3"] = 0
    results["part4"] = 0
    results["part5"] = 0
    for i,ans in enumerate(data.part1):
        if answers.part1[i].lower() == ans.lower():
            results["part1"]+=1
    for i, ans in enumerate(data.part2):
        if answers.part2[i].lower() == ans.lower():
            results["part2"]+=1
    for i, ans in enumerate(data.part3):
        if answers.part3[i].lower() == ans.lower():
            results["part3"]+=1
    for i, ans in enumerate(data.part4):
        if answers.part4[i].lower() == ans.lower():
            results["part4"]+=1
    for i, ans in enumerate(data.part5):
        if answers.part5[i].lower() == ans.lower():
            results["part5"]+=1
    return results