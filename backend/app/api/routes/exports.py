import csv
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import CalendarFeedToken, Session as SessionModel, Student, Teacher, User
from app.schemas.calendar import CalendarFeedTokenCreate, CalendarFeedTokenRead
from app.services.access import AccessScope, apply_session_scope, ensure_calendar_owner_access, get_calendar_feed_or_404
from app.services.audit import write_audit_log
from app.services.calendar import build_ics_calendar, hash_feed_token, issue_feed_token
from app.services.scheduling import build_occurrences


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/sessions.csv")
def export_sessions_csv(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> StreamingResponse:
    sessions = list(
        db.scalars(
            apply_session_scope(select(SessionModel), scope).order_by(SessionModel.weekday, SessionModel.start_minute)
        )
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "teacher_id",
            "student_id",
            "weekday",
            "start_minute",
            "end_minute",
            "duration_minutes",
            "subject",
            "status",
            "start_date",
            "end_date",
            "notes",
        ]
    )
    for row in sessions:
        writer.writerow(
            [
                row.id,
                row.teacher_id,
                row.student_id,
                row.weekday,
                row.start_minute,
                row.end_minute,
                row.duration_minutes,
                row.subject,
                row.status,
                row.start_date.isoformat(),
                row.end_date.isoformat() if row.end_date else "",
                row.notes,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions.csv"},
    )


def _build_calendar_occurrences(db: Session, owner_type: str, owner_id: int | None):
    filters = {}
    if owner_type == "teacher":
        filters["teacher_id"] = owner_id
    elif owner_type == "student":
        filters["student_id"] = owner_id
    elif owner_type != "centre":
        raise HTTPException(status_code=400, detail="owner_type must be teacher, student, or centre")
    today = date.today()
    return build_occurrences(db, date_from=today, date_to=today + timedelta(days=365), **filters)


@router.get("/calendar/{owner_type}/{owner_id}.ics")
def export_calendar_file(
    owner_type: str,
    owner_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> Response:
    ensure_calendar_owner_access(db, scope, owner_type=owner_type, owner_id=owner_id)
    calendar_bytes = build_ics_calendar(f"{owner_type}-{owner_id}", _build_calendar_occurrences(db, owner_type, owner_id))
    return Response(
        content=calendar_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={owner_type}-{owner_id}.ics"},
    )


@router.post("/calendar-feeds", response_model=CalendarFeedTokenRead, status_code=status.HTTP_201_CREATED)
def create_calendar_feed_token(
    payload: CalendarFeedTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> CalendarFeedTokenRead:
    if payload.owner_type == "teacher" and db.get(Teacher, payload.owner_id) is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if payload.owner_type == "student" and db.get(Student, payload.owner_id) is None:
        raise HTTPException(status_code=404, detail="Student not found")
    token = issue_feed_token()
    record = CalendarFeedToken(
        owner_type=payload.owner_type,
        owner_id=payload.owner_id,
        label=payload.label,
        token_hash=hash_feed_token(token),
        created_by_user_id=current_user.id,
    )
    db.add(record)
    db.flush()
    write_audit_log(
        db,
        action="calendar.feed.created",
        entity_type="calendar_feed",
        entity_id=str(record.id),
        summary="Calendar feed token created",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    return CalendarFeedTokenRead(
        id=record.id,
        owner_type=record.owner_type,
        owner_id=record.owner_id,
        label=record.label,
        active=record.active,
        token=token,
    )


@router.delete("/calendar-feeds/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_calendar_feed_token(
    feed_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    record = get_calendar_feed_or_404(db, feed_id)
    record.active = False
    db.add(record)
    write_audit_log(
        db,
        action="calendar.feed.revoked",
        entity_type="calendar_feed",
        entity_id=str(record.id),
        summary="Calendar feed revoked",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()


@router.get("/calendar-feed/{token}.ics")
def export_calendar_feed(token: str, db: Session = Depends(get_db)) -> Response:
    feed = db.scalar(
        select(CalendarFeedToken).where(
            CalendarFeedToken.token_hash == hash_feed_token(token),
            CalendarFeedToken.active.is_(True),
        )
    )
    if feed is None:
        raise HTTPException(status_code=404, detail="Calendar feed not found")
    calendar_bytes = build_ics_calendar(feed.label or feed.owner_type, _build_calendar_occurrences(db, feed.owner_type, feed.owner_id))
    return Response(content=calendar_bytes, media_type="text/calendar")
