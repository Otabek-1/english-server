from datetime import date, datetime, timedelta
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.auth import get_current_user
from database.db import IeltsSubmission, MockAttempt, MockProgress, User, WritingResult, get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


QUOTES = [
    "A weak day with one mock still beats a perfect plan that never starts.",
    "Momentum is built by finishing today's test before tomorrow's excuses arrive.",
    "Every unfinished skill becomes visible the moment the timer starts.",
    "Discipline grows when you practice under pressure, not when you wait for motivation.",
    "Mock by mock, panic turns into pattern recognition.",
    "If you can face the timer daily, the real exam loses its power over you.",
    "One serious attempt today is worth more than seven days of thinking about it.",
    "Your score changes when your routine stops negotiating with comfort.",
    "The gap closes fastest when you train the skill you avoid most.",
    "A streak is proof that your future score is already being built.",
    "Pressure is not the enemy. Unfamiliar pressure is.",
    "The student who returns after a bad mock improves faster than the student who waits for a good day.",
]

SKILL_ORDER = ["listening", "reading", "writing", "speaking"]


class ProgressUpsertPayload(BaseModel):
    exam_type: str = Field(min_length=3, max_length=50)
    skill_area: Optional[str] = Field(default=None, max_length=20)
    mock_id: Optional[str] = Field(default=None, max_length=80)
    title: Optional[str] = Field(default=None, max_length=180)
    route_path: str = Field(min_length=1, max_length=255)
    remaining_seconds: Optional[int] = Field(default=None, ge=0, le=43200)
    progress_state: Dict[str, Any] = Field(default_factory=dict)


class ProgressCompletePayload(BaseModel):
    exam_type: str = Field(min_length=3, max_length=50)
    mock_id: Optional[str] = Field(default=None, max_length=80)


class AttemptPayload(BaseModel):
    exam_type: str = Field(min_length=3, max_length=50)
    skill_area: Optional[str] = Field(default=None, max_length=20)
    mock_id: Optional[str] = Field(default=None, max_length=80)
    title: Optional[str] = Field(default=None, max_length=180)
    route_path: Optional[str] = Field(default=None, max_length=255)
    score: Optional[int] = Field(default=None, ge=0)
    max_score: Optional[int] = Field(default=None, ge=0)
    score_percent: Optional[int] = Field(default=None, ge=0, le=100)
    score_75: Optional[int] = Field(default=None, ge=0, le=75)
    band: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(default="completed", max_length=30)
    attempt_meta: Dict[str, Any] = Field(default_factory=dict)
    clear_progress: bool = True


class FullMockAttemptPayload(BaseModel):
    overall_score_75: int = Field(ge=0, le=75)
    route_path: Optional[str] = Field(default="/mock/cefr/full", max_length=255)
    title: Optional[str] = Field(default="CEFR Full Mock", max_length=180)
    section_scores: Dict[str, int] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)


class AttemptResolvePayload(BaseModel):
    exam_type: str = Field(min_length=3, max_length=50)
    mock_id: Optional[str] = Field(default=None, max_length=80)
    score: Optional[int] = Field(default=None, ge=0)
    max_score: Optional[int] = Field(default=None, ge=0)
    score_percent: Optional[int] = Field(default=None, ge=0, le=100)
    score_75: Optional[int] = Field(default=None, ge=0, le=75)
    band: Optional[str] = Field(default=None, max_length=20)
    title: Optional[str] = Field(default=None, max_length=180)
    route_path: Optional[str] = Field(default=None, max_length=255)
    attempt_meta: Dict[str, Any] = Field(default_factory=dict)


def clamp(num: Optional[float], low: int, high: int) -> Optional[int]:
    if num is None:
        return None
    return max(low, min(high, int(round(num))))


def normalize_score_75(score: Optional[int], max_score: Optional[int], score_percent: Optional[int], score_75: Optional[int]) -> Optional[int]:
    if score_75 is not None:
        return clamp(score_75, 0, 75)
    if score_percent is not None:
        return clamp((score_percent / 100) * 75, 0, 75)
    if score is not None and max_score:
        return clamp((score / max_score) * 75, 0, 75)
    return None


def serialize_progress(row: MockProgress) -> Dict[str, Any]:
    return {
        "id": row.id,
        "exam_type": row.exam_type,
        "skill_area": row.skill_area,
        "mock_id": row.mock_id,
        "title": row.title,
        "route_path": row.route_path,
        "status": row.status,
        "remaining_seconds": row.remaining_seconds,
        "progress_state": row.progress_state or {},
        "started_at": row.started_at,
        "last_activity_at": row.last_activity_at,
    }


def serialize_attempt(row: MockAttempt) -> Dict[str, Any]:
    return {
        "id": row.id,
        "exam_type": row.exam_type,
        "skill_area": row.skill_area,
        "mock_id": row.mock_id,
        "title": row.title,
        "route_path": row.route_path,
        "score": row.score,
        "max_score": row.max_score,
        "score_percent": row.score_percent,
        "score_75": row.score_75,
        "band": row.band,
        "status": row.status,
        "created_at": row.created_at,
        "meta": row.attempt_meta or {},
    }


def upsert_progress_row(db: Session, user_id: int, payload: ProgressUpsertPayload) -> MockProgress:
    row = (
        db.query(MockProgress)
        .filter(
            MockProgress.user_id == user_id,
            MockProgress.exam_type == payload.exam_type,
            MockProgress.mock_id == payload.mock_id,
            MockProgress.status == "active",
        )
        .order_by(MockProgress.id.desc())
        .first()
    )
    if not row:
        row = MockProgress(
            user_id=user_id,
            exam_type=payload.exam_type,
            skill_area=payload.skill_area,
            mock_id=payload.mock_id,
            title=payload.title,
            route_path=payload.route_path,
            remaining_seconds=payload.remaining_seconds,
            progress_state=payload.progress_state,
        )
        db.add(row)
    else:
        row.skill_area = payload.skill_area
        row.title = payload.title
        row.route_path = payload.route_path
        row.remaining_seconds = payload.remaining_seconds
        row.progress_state = payload.progress_state
        row.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def complete_progress_rows(db: Session, user_id: int, exam_type: str, mock_id: Optional[str]) -> None:
    rows = (
        db.query(MockProgress)
        .filter(
            MockProgress.user_id == user_id,
            MockProgress.exam_type == exam_type,
            MockProgress.status == "active",
            MockProgress.mock_id == mock_id,
        )
        .all()
    )
    for row in rows:
        row.status = "completed"
        row.completed_at = datetime.utcnow()
        row.last_activity_at = datetime.utcnow()
    db.commit()


def create_attempt_row(db: Session, user_id: int, payload: AttemptPayload) -> MockAttempt:
    row = MockAttempt(
        user_id=user_id,
        exam_type=payload.exam_type,
        skill_area=payload.skill_area,
        mock_id=payload.mock_id,
        title=payload.title,
        route_path=payload.route_path,
        score=payload.score,
        max_score=payload.max_score,
        score_percent=payload.score_percent,
        score_75=normalize_score_75(payload.score, payload.max_score, payload.score_percent, payload.score_75),
        band=payload.band,
        status=payload.status,
        attempt_meta=payload.attempt_meta,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if payload.clear_progress:
        complete_progress_rows(db=db, user_id=user_id, exam_type=payload.exam_type, mock_id=payload.mock_id)
    return row


def resolve_latest_attempt_row(db: Session, user_id: int, payload: AttemptResolvePayload) -> MockAttempt:
    row = (
        db.query(MockAttempt)
        .filter(
            MockAttempt.user_id == user_id,
            MockAttempt.exam_type == payload.exam_type,
            MockAttempt.mock_id == payload.mock_id,
        )
        .order_by(MockAttempt.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if payload.title is not None:
        row.title = payload.title
    if payload.route_path is not None:
        row.route_path = payload.route_path
    row.score = payload.score
    row.max_score = payload.max_score
    row.score_percent = payload.score_percent
    row.score_75 = normalize_score_75(payload.score, payload.max_score, payload.score_percent, payload.score_75)
    row.band = payload.band
    row.status = "completed"
    row.attempt_meta = {**(row.attempt_meta or {}), **(payload.attempt_meta or {})}
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def attempt_to_skill_values(attempts: List[MockAttempt]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {
        skill: {"score": 0, "attempts": 0, "last_score": None}
        for skill in SKILL_ORDER
    }
    grouped: Dict[str, List[MockAttempt]] = {skill: [] for skill in SKILL_ORDER}
    for attempt in attempts:
        if attempt.skill_area in grouped and attempt.score_75 is not None:
            grouped[attempt.skill_area].append(attempt)

    for skill in SKILL_ORDER:
        rows = grouped[skill][:5]
        if not rows:
            continue
        weights = [1.0, 0.85, 0.7, 0.55, 0.4]
        weighted_sum = 0.0
        total_weight = 0.0
        for idx, row in enumerate(rows):
            weight = weights[idx]
            weighted_sum += row.score_75 * weight
            total_weight += weight
        score = int(round((weighted_sum / total_weight) * (100 / 75))) if total_weight else 0
        result[skill] = {
            "score": clamp(score, 0, 100) or 0,
            "attempts": len(grouped[skill]),
            "last_score": rows[0].score_75,
        }
    return result


def calculate_streak(attempts: List[MockAttempt]) -> Dict[str, Any]:
    unique_days = sorted({row.created_at.date() for row in attempts}, reverse=True)
    today = datetime.utcnow().date()
    streak = 0
    cursor = today
    while cursor in unique_days:
        streak += 1
        cursor = cursor - timedelta(days=1)

    this_week = sum(1 for row in attempts if row.created_at.date() >= today - timedelta(days=6))
    return {
        "current": streak,
        "this_week": this_week,
        "last_active_date": unique_days[0].isoformat() if unique_days else None,
    }


def build_focus_cards(attempts: List[MockAttempt], skill_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    weekday_skill = SKILL_ORDER[datetime.utcnow().weekday() % len(SKILL_ORDER)]
    weakest_skill = min(SKILL_ORDER, key=lambda skill: skill_scores[skill]["score"] or 0)
    latest_attempt = attempts[0] if attempts else None

    focus = {
        "title": f"Today is {weekday_skill.title()} day",
        "body": "Short, focused repetition beats rare marathon practice. Give this skill one serious timed attempt today.",
        "button_label": f"Practice {weekday_skill.title()}",
        "route_path": {
            "listening": "/dashboard?tab=cefr_listening",
            "reading": "/dashboard?tab=cefr_reading",
            "writing": "/dashboard?tab=cefr_writing",
            "speaking": "/dashboard?tab=cefr_speaking",
        }.get(weekday_skill, "/dashboard"),
        "skill_area": weekday_skill,
    }

    if weakest_skill and weakest_skill != weekday_skill:
        focus["secondary"] = {
            "title": f"Weakest signal: {weakest_skill.title()}",
            "body": "Your dashboard is pointing at the skill that needs pressure-tested repetition most.",
            "skill_area": weakest_skill,
        }

    trend = {
        "title": "Today's trend: CEFR full mock",
        "body": "If you want the clearest performance signal, run a full sequence under time pressure.",
        "button_label": "Try Full Mock",
        "route_path": "/mock/cefr/full",
    }

    if latest_attempt and latest_attempt.skill_area:
        trend = {
            "title": f"Recent momentum: {latest_attempt.skill_area.title()}",
            "body": "Come back to the same pressure zone before the pattern fades. Consistency compounds faster than intensity.",
            "button_label": f"Go Again",
            "route_path": latest_attempt.route_path or "/dashboard",
        }

    return {"focus": focus, "trend": trend}


@router.get("/progress/active")
def get_active_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(MockProgress)
        .filter(MockProgress.user_id == current_user.id, MockProgress.status == "active")
        .order_by(MockProgress.last_activity_at.desc(), MockProgress.id.desc())
        .first()
    )
    return {"progress": serialize_progress(row) if row else None}


@router.get("/progress/lookup")
def lookup_progress(
    exam_type: str = Query(...),
    mock_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(MockProgress)
        .filter(
            MockProgress.user_id == current_user.id,
            MockProgress.exam_type == exam_type,
            MockProgress.mock_id == mock_id,
            MockProgress.status == "active",
        )
        .order_by(MockProgress.last_activity_at.desc(), MockProgress.id.desc())
        .first()
    )
    return {"progress": serialize_progress(row) if row else None}


@router.post("/progress")
def save_progress(
    payload: ProgressUpsertPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = upsert_progress_row(db=db, user_id=current_user.id, payload=payload)
    return {"progress": serialize_progress(row)}


@router.post("/progress/complete")
def complete_progress(
    payload: ProgressCompletePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    complete_progress_rows(db=db, user_id=current_user.id, exam_type=payload.exam_type, mock_id=payload.mock_id)
    return {"success": True}


@router.post("/attempts")
def create_attempt(
    payload: AttemptPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = create_attempt_row(db=db, user_id=current_user.id, payload=payload)
    return {"attempt": serialize_attempt(row)}


@router.post("/attempts/full-mock")
def create_full_mock_attempt(
    payload: FullMockAttemptPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    full_attempt = MockAttempt(
        user_id=current_user.id,
        exam_type="cefr_full_mock",
        skill_area=None,
        mock_id="full",
        title=payload.title,
        route_path=payload.route_path,
        score_75=payload.overall_score_75,
        score_percent=clamp((payload.overall_score_75 / 75) * 100, 0, 100),
        status="completed",
        attempt_meta={
            "section_scores": payload.section_scores,
            "details": payload.details,
        },
    )
    db.add(full_attempt)

    for skill, score in payload.section_scores.items():
        if skill not in SKILL_ORDER:
            continue
        db.add(
            MockAttempt(
                user_id=current_user.id,
                exam_type=f"cefr_full_{skill}",
                skill_area=skill,
                mock_id="full",
                title=f"CEFR Full Mock - {skill.title()}",
                route_path=payload.route_path,
                score_75=clamp(score, 0, 75),
                score_percent=clamp((score / 75) * 100, 0, 100),
                status="completed",
                attempt_meta={"source": "cefr_full_mock"},
            )
        )

    complete_progress_rows(db=db, user_id=current_user.id, exam_type="cefr_full_mock", mock_id="full")
    db.commit()
    db.refresh(full_attempt)
    return {"attempt": serialize_attempt(full_attempt)}


@router.patch("/attempts/latest")
def resolve_latest_attempt(
    payload: AttemptResolvePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = resolve_latest_attempt_row(db=db, user_id=current_user.id, payload=payload)
    return {"attempt": serialize_attempt(row)}


@router.get("/home")
def get_dashboard_home(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active_progress = (
        db.query(MockProgress)
        .filter(MockProgress.user_id == current_user.id, MockProgress.status == "active")
        .order_by(MockProgress.last_activity_at.desc(), MockProgress.id.desc())
        .first()
    )
    attempts = (
        db.query(MockAttempt)
        .filter(MockAttempt.user_id == current_user.id)
        .order_by(MockAttempt.created_at.desc(), MockAttempt.id.desc())
        .limit(30)
        .all()
    )

    skill_scores = attempt_to_skill_values(attempts)
    streak = calculate_streak(attempts)
    cards = build_focus_cards(attempts, skill_scores)

    pending_writing = (
        db.query(WritingResult)
        .filter(WritingResult.user_id == current_user.id, WritingResult.result.is_(None))
        .count()
    )
    ielts_count = db.query(IeltsSubmission).filter(IeltsSubmission.user_id == current_user.id).count()

    random.seed(f"{current_user.id}-{date.today().isoformat()}")
    quote = random.choice(QUOTES)

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "premium_until": current_user.premium_duration,
        },
        "quote": quote,
        "streak": streak,
        "skill_scores": skill_scores,
        "active_progress": serialize_progress(active_progress) if active_progress else None,
        "history": [serialize_attempt(row) for row in attempts[:10]],
        "cards": cards,
        "stats": {
            "attempts_total": len(attempts),
            "pending_writing_reviews": pending_writing,
            "ielts_submissions": ielts_count,
        },
    }
