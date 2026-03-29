from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.auth import verify_role
from database.db import User, get_db
from services.request_monitor import get_traffic_snapshot

router = APIRouter(prefix="/dashboard/admin/traffic", tags=["traffic-monitor"])


@router.get("")
def get_admin_traffic_snapshot(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=25, ge=5, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_role(["admin"])),
):
    return get_traffic_snapshot(db=db, hours=hours, limit=limit)
