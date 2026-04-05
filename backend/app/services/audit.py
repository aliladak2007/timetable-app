from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit_log(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    actor_user_id: int | None = None,
    actor_email: str = "",
    outcome: str = "success",
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome=outcome,
            summary=summary,
            details=details or {},
        )
    )
