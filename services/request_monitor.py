from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from database.db import RequestAuditLog

EXCLUDED_PATH_PREFIXES = (
    "/dashboard/admin/traffic",
    "/docs",
    "/openapi.json",
)


def extract_client_ip(headers: dict[str, str], fallback_ip: str | None) -> tuple[str | None, str | None]:
    forwarded_for = headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip or fallback_ip, forwarded_for
    real_ip = headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip(), forwarded_for
    return fallback_ip, forwarded_for


def normalize_origin(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return value


def should_skip_logging(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)


def build_risk_flags(headers: dict[str, str], host: str | None, origin: str | None, referer: str | None) -> list[str]:
    flags: list[str] = []
    normalized_origin = normalize_origin(origin)
    normalized_referer = normalize_origin(referer)
    host_value = (host or "").lower()

    if normalized_origin and host_value and host_value not in normalized_origin.lower():
        flags.append("cross_origin")
    if normalized_referer and host_value and host_value not in normalized_referer.lower():
        flags.append("external_referer")
    if not origin and referer:
        flags.append("missing_origin")
    if headers.get("sec-fetch-site") == "cross-site":
        flags.append("cross_site_fetch")
    if headers.get("authorization"):
        flags.append("auth_used")

    return flags


def create_audit_log(
    db: Session,
    *,
    method: str,
    path: str,
    query_string: str,
    full_url: str,
    status_code: int,
    client_ip: str | None,
    forwarded_for: str | None,
    host: str | None,
    origin: str | None,
    referer: str | None,
    user_agent: str | None,
    scheme: str | None,
    request_headers: dict[str, Any],
) -> None:
    log = RequestAuditLog(
        method=method,
        path=path,
        query_string=query_string or None,
        full_url=full_url,
        status_code=status_code,
        client_ip=client_ip,
        forwarded_for=forwarded_for,
        host=host,
        origin=normalize_origin(origin),
        referer=referer,
        user_agent=user_agent,
        scheme=scheme,
        request_headers=request_headers,
        risk_flags=build_risk_flags(request_headers, host, origin, referer),
    )
    db.add(log)
    db.commit()


def _top_group(
    db: Session,
    column: Any,
    *,
    since: datetime,
    limit: int,
    exclude_null: bool = True,
) -> list[dict[str, Any]]:
    query = (
        db.query(column.label("value"), func.count(RequestAuditLog.id).label("count"))
        .filter(RequestAuditLog.created_at >= since)
    )
    if exclude_null:
        query = query.filter(column.isnot(None)).filter(column != "")
    rows = query.group_by(column).order_by(desc("count")).limit(limit).all()
    return [{"value": value, "count": count} for value, count in rows]


def get_traffic_snapshot(db: Session, *, hours: int = 24, limit: int = 20) -> dict[str, Any]:
    safe_hours = max(1, min(hours, 168))
    safe_limit = max(5, min(limit, 100))
    since = datetime.utcnow() - timedelta(hours=safe_hours)

    total_requests = db.query(func.count(RequestAuditLog.id)).filter(RequestAuditLog.created_at >= since).scalar() or 0
    unique_ips = (
        db.query(func.count(func.distinct(RequestAuditLog.client_ip)))
        .filter(RequestAuditLog.created_at >= since)
        .scalar()
        or 0
    )
    unique_origins = (
        db.query(func.count(func.distinct(RequestAuditLog.origin)))
        .filter(RequestAuditLog.created_at >= since, RequestAuditLog.origin.isnot(None), RequestAuditLog.origin != "")
        .scalar()
        or 0
    )
    suspicious_rows = (
        db.query(RequestAuditLog.risk_flags)
        .filter(RequestAuditLog.created_at >= since)
        .all()
    )
    suspicious_requests = sum(1 for (risk_flags,) in suspicious_rows if risk_flags)

    recent_rows = (
        db.query(RequestAuditLog)
        .filter(RequestAuditLog.created_at >= since)
        .order_by(RequestAuditLog.created_at.desc(), RequestAuditLog.id.desc())
        .limit(safe_limit)
        .all()
    )

    blocked_like = (
        db.query(func.count(RequestAuditLog.id))
        .filter(RequestAuditLog.created_at >= since, RequestAuditLog.status_code >= 400)
        .scalar()
        or 0
    )

    return {
        "window_hours": safe_hours,
        "summary": {
            "total_requests": total_requests,
            "unique_ips": unique_ips,
            "unique_origins": unique_origins,
            "suspicious_requests": suspicious_requests,
            "error_responses": blocked_like,
        },
        "top_paths": _top_group(db, RequestAuditLog.path, since=since, limit=10),
        "top_ips": _top_group(db, RequestAuditLog.client_ip, since=since, limit=10),
        "top_origins": _top_group(db, RequestAuditLog.origin, since=since, limit=10),
        "top_hosts": _top_group(db, RequestAuditLog.host, since=since, limit=10),
        "top_user_agents": _top_group(db, RequestAuditLog.user_agent, since=since, limit=8),
        "recent_requests": [
            {
                "id": row.id,
                "created_at": row.created_at,
                "method": row.method,
                "path": row.path,
                "query_string": row.query_string,
                "status_code": row.status_code,
                "client_ip": row.client_ip,
                "forwarded_for": row.forwarded_for,
                "host": row.host,
                "origin": row.origin,
                "referer": row.referer,
                "scheme": row.scheme,
                "user_agent": row.user_agent,
                "risk_flags": row.risk_flags or [],
            }
            for row in recent_rows
        ],
    }
