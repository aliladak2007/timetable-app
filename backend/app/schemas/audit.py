from app.schemas.common import ORMModel, TimestampedRead


class AuditLogRead(TimestampedRead, ORMModel):
    id: int
    actor_user_id: int | None = None
    actor_email: str
    action: str
    entity_type: str
    entity_id: str
    outcome: str
    summary: str
    details: dict
