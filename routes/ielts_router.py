from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from auth.auth import get_current_user, verify_role
from database.db import IeltsSection, IeltsSubmission, IeltsTest, User, get_db
from schemas.ielts_schema import IeltsModuleResult, IeltsOverview, IeltsSubmissionCreate, IeltsTestCreate, IeltsTestUpdate

router = APIRouter(prefix="/ielts", tags=["IELTS"])


def _normalize_answer(value: str) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def _score_to_band(module: str, score: int, total: int) -> Optional[str]:
    if total <= 0:
        return None

    # IELTS listening/reading style approximation
    ratio = score / total
    if ratio >= 0.975:
        return "9.0"
    if ratio >= 0.925:
        return "8.5"
    if ratio >= 0.875:
        return "8.0"
    if ratio >= 0.825:
        return "7.5"
    if ratio >= 0.75:
        return "7.0"
    if ratio >= 0.675:
        return "6.5"
    if ratio >= 0.60:
        return "6.0"
    if ratio >= 0.525:
        return "5.5"
    if ratio >= 0.45:
        return "5.0"
    if ratio >= 0.375:
        return "4.5"
    if ratio >= 0.30:
        return "4.0"
    return "3.5"


def _serialize_section(section: IeltsSection) -> Dict:
    return {
        "id": section.id,
        "module": section.module,
        "title": section.title,
        "instructions": section.instructions,
        "duration_minutes": section.duration_minutes,
        "content": section.content,
        "order_index": section.order_index,
    }


def _serialize_test(test: IeltsTest, include_answers: bool = False) -> Dict:
    serialized_sections = []
    for section in test.sections:
        section_data = _serialize_section(section)
        if include_answers:
            section_data["answer_key"] = section.answer_key
        serialized_sections.append(section_data)

    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "exam_track": test.exam_track,
        "level": test.level,
        "duration_minutes": test.duration_minutes,
        "is_published": test.is_published,
        "tags": test.tags or [],
        "meta": test.meta or {},
        "created_at": test.created_at,
        "updated_at": test.updated_at,
        "sections": serialized_sections,
    }


@router.get("/overview", response_model=IeltsOverview)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    published_tests = db.query(IeltsTest).filter(IeltsTest.is_published.is_(True)).count()
    my_submissions = (
        db.query(IeltsSubmission)
        .filter(IeltsSubmission.user_id == current_user.id)
        .order_by(IeltsSubmission.id.desc())
        .all()
    )

    latest_band = None
    for submission in my_submissions:
        if submission.band:
            latest_band = submission.band
            break

    module_rows = db.query(IeltsSection.module).distinct().all()
    modules = sorted({row[0] for row in module_rows})

    return IeltsOverview(
        published_tests=published_tests,
        total_submissions=len(my_submissions),
        latest_band=latest_band,
        modules_available=modules,
    )


@router.get("/tests")
def list_tests(
    module: Optional[str] = Query(default=None),
    exam_track: Optional[str] = Query(default=None),
    published_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(IeltsTest).options(selectinload(IeltsTest.sections))

    if published_only and current_user.role != "admin":
        query = query.filter(IeltsTest.is_published.is_(True))
    elif published_only:
        query = query.filter(IeltsTest.is_published.is_(True))

    if exam_track:
        query = query.filter(IeltsTest.exam_track == exam_track)

    tests = query.order_by(IeltsTest.id.desc()).all()
    if module:
        tests = [test for test in tests if any(section.module == module for section in test.sections)]

    return {"tests": [_serialize_test(test, include_answers=False) for test in tests]}


@router.get("/tests/{test_id}")
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = (
        db.query(IeltsTest)
        .options(selectinload(IeltsTest.sections))
        .filter(IeltsTest.id == test_id)
        .first()
    )
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IELTS test not found")

    if not test.is_published and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test is not published")

    return {"test": _serialize_test(test, include_answers=current_user.role == "admin")}


@router.post("/tests")
def create_test(
    data: IeltsTestCreate,
    db: Session = Depends(get_db),
    _: User = Depends(verify_role(["admin"])),
):
    test = IeltsTest(
        title=data.title,
        description=data.description,
        exam_track=data.exam_track,
        level=data.level,
        duration_minutes=data.duration_minutes,
        is_published=data.is_published,
        tags=data.tags,
        meta=data.meta,
    )
    db.add(test)
    db.flush()

    for section in data.sections:
        db.add(
            IeltsSection(
                test_id=test.id,
                module=section.module,
                title=section.title,
                instructions=section.instructions,
                duration_minutes=section.duration_minutes,
                content=section.content,
                answer_key=section.answer_key,
                order_index=section.order_index,
            )
        )

    db.commit()
    db.refresh(test)
    return {"message": "IELTS test created", "test_id": test.id}


@router.put("/tests/{test_id}")
def update_test(
    test_id: int,
    data: IeltsTestUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(verify_role(["admin"])),
):
    test = db.query(IeltsTest).filter(IeltsTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IELTS test not found")

    test.title = data.title
    test.description = data.description
    test.exam_track = data.exam_track
    test.level = data.level
    test.duration_minutes = data.duration_minutes
    test.is_published = data.is_published
    test.tags = data.tags
    test.meta = data.meta
    test.updated_at = datetime.utcnow()

    db.query(IeltsSection).filter(IeltsSection.test_id == test_id).delete(synchronize_session=False)

    for section in data.sections:
        db.add(
            IeltsSection(
                test_id=test.id,
                module=section.module,
                title=section.title,
                instructions=section.instructions,
                duration_minutes=section.duration_minutes,
                content=section.content,
                answer_key=section.answer_key,
                order_index=section.order_index,
            )
        )

    db.commit()
    return {"message": "IELTS test updated"}


@router.delete("/tests/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_role(["admin"])),
):
    test = db.query(IeltsTest).filter(IeltsTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IELTS test not found")

    db.delete(test)
    db.commit()
    return {"message": "IELTS test deleted"}


@router.post("/tests/{test_id}/submit/{module}", response_model=IeltsModuleResult)
def submit_module(
    test_id: int,
    module: str,
    data: IeltsSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = (
        db.query(IeltsSection)
        .join(IeltsTest, IeltsTest.id == IeltsSection.test_id)
        .filter(IeltsSection.test_id == test_id, IeltsSection.module == module)
        .first()
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IELTS section not found")

    score = None
    max_score = None
    band = None
    feedback: Dict = {
        "submitted_answers": len(data.answers or []),
        "module": module,
    }

    answer_key = section.answer_key or []
    if module in {"reading", "listening"} and answer_key:
        normalized_user = [_normalize_answer(item) for item in data.answers]
        normalized_key = [_normalize_answer(item) for item in answer_key]

        max_score = len(normalized_key)
        score = 0
        mismatches = []
        for idx, correct in enumerate(normalized_key):
            user_ans = normalized_user[idx] if idx < len(normalized_user) else ""
            if user_ans == correct:
                score += 1
            else:
                mismatches.append(
                    {
                        "question": idx + 1,
                        "expected": answer_key[idx],
                        "received": data.answers[idx] if idx < len(data.answers) else "",
                    }
                )
        band = _score_to_band(module, score, max_score)
        feedback["mismatches"] = mismatches
        feedback["accuracy"] = round((score / max_score) * 100, 2) if max_score else 0
    else:
        feedback["status"] = "pending_manual_review"
        if data.ai_feedback:
            feedback["ai_feedback"] = data.ai_feedback
            ai_band = data.ai_feedback.get("band")
            if isinstance(ai_band, (str, int, float)):
                band = str(ai_band)

    submission = IeltsSubmission(
        user_id=current_user.id,
        test_id=test_id,
        module=module,
        answers=data.answers,
        score=score,
        max_score=max_score,
        band=band,
        feedback=feedback,
        time_spent_seconds=data.time_spent_seconds,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return IeltsModuleResult(
        score=submission.score,
        max_score=submission.max_score,
        band=submission.band,
        feedback=submission.feedback or {},
        submission_id=submission.id,
    )


@router.get("/submissions/me")
def my_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(IeltsSubmission, IeltsTest)
        .join(IeltsTest, IeltsTest.id == IeltsSubmission.test_id)
        .filter(IeltsSubmission.user_id == current_user.id)
        .order_by(IeltsSubmission.id.desc())
        .all()
    )

    return {
        "submissions": [
            {
                "id": submission.id,
                "module": submission.module,
                "score": submission.score,
                "max_score": submission.max_score,
                "band": submission.band,
                "time_spent_seconds": submission.time_spent_seconds,
                "created_at": submission.created_at,
                "test": {
                    "id": test.id,
                    "title": test.title,
                    "exam_track": test.exam_track,
                },
                "feedback": submission.feedback or {},
            }
            for submission, test in rows
        ]
    }


@router.get("/submissions/admin")
def all_submissions_admin(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(verify_role(["admin"])),
):
    rows = (
        db.query(IeltsSubmission, IeltsTest, User)
        .join(IeltsTest, IeltsTest.id == IeltsSubmission.test_id)
        .join(User, User.id == IeltsSubmission.user_id)
        .order_by(IeltsSubmission.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "submissions": [
            {
                "id": submission.id,
                "module": submission.module,
                "score": submission.score,
                "max_score": submission.max_score,
                "band": submission.band,
                "time_spent_seconds": submission.time_spent_seconds,
                "created_at": submission.created_at,
                "feedback": submission.feedback or {},
                "test": {
                    "id": test.id,
                    "title": test.title,
                },
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            }
            for submission, test, user in rows
        ]
    }
