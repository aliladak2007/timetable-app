from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import Session as SessionModel, User
from app.schemas.session import SessionCreate, SessionRead, SessionUpdate
from app.services.access import AccessScope, apply_session_scope, ensure_teacher_access, get_session_or_404
from app.services.audit import write_audit_log
from app.services.booking import validate_session_booking


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRead])
def list_sessions(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[SessionModel]:
    return list(
        db.scalars(
            apply_session_scope(select(SessionModel), scope).order_by(SessionModel.weekday, SessionModel.start_minute)
        )
    )


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> SessionModel:
    ensure_teacher_access(scope, payload.teacher_id)
    errors = validate_session_booking(db, payload)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    session = SessionModel(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(session)
    db.flush()
    write_audit_log(
        db,
        action="session.created",
        entity_type="session",
        entity_id=str(session.id),
        summary=f"Recurring session created for teacher {payload.teacher_id} and student {payload.student_id}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}", response_model=SessionRead)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> SessionModel:
    session = get_session_or_404(db, scope, session_id)

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(session, key, value)
    db.add(session)
    write_audit_log(
        db,
        action="session.updated",
        entity_type="session",
        entity_id=str(session.id),
        summary="Recurring session updated",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=changes,
    )
    db.commit()
    db.refresh(session)
    return session
