"""Audit logging helpers. Audit records are append-only by application design."""

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def write_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id: str | int | None = None,
    reason: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    record = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        reason=reason,
        before_data=before,
        after_data=after,
        ip_address=request.client.host if request and request.client else None,
        user_agent=(request.headers.get("user-agent")[:500] if request else None),
    )
    db.add(record)
    return record
