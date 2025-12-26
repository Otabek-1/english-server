from fastapi import APIRouter, Depends, status, HTTPException
from database.db import get_db, User, ListeningMock, ListeningMockAnswer
from auth.auth import verify_access_token, verify_role
from schemas.listeningSchema import ListeningMockSchema, ListeningMockAnswersSchema
from sqlalchemy.orm import Session

router = APIRouter(prefix="/cefr/listening", tags=["Listening"])

@router.get("/all")
def get_all_mocks(db:Session = Depends(get_db)):
    res = db.query(ListeningMock).all()
    return res

@router.get("/{id}")
def get_listening(id:int,db: Session = Depends(get_db)):
    res = db.query(ListeningMock).filter(ListeningMock.id == id).first()
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
def get_by_mock_id(mock_id:int, db: Session = Depends(get_db)):
    res=  db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == mock_id).first()
    return res

@router.post("/answer/create/{mock_id}")
def add_answer(mock_id:int, data:ListeningMockAnswersSchema ,db: Session = Depends(get_db), user=Depends(verify_role(["admin"]))):
    new = ListeningMockAnswer(mock_id=mock_id, part_1=data.part_1,part_2=data.part_2,part_3=data.part_3,part_4=data.part_4,part_5=data.part_5,part_6=data.part_6)
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"message":"Success"}

@router.put("/answer/update/{mock_id}")
def update_answers(mock_id:int, data: ListeningMockAnswersSchema, db: Session = Depends(get_db), user=Depends(verify_role(['admin']))):
    res = db.query(ListeningMockAnswer).filter(ListeningMockAnswer.mock_id == mock_id).first()
    res.part_1 = data.part_1
    res.part_2 = data.part_2
    res.part_3 = data.part_3
    res.part_4 = data.part_4
    res.part_5 = data.part_5
    res.part_6 = data.part_6
    db.commit()
    db.refresh(res)
    return {"message":"Success"}
