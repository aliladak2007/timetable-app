from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import CentreClosure, SessionOccurrenceException, StudentAbsence, TeacherLeave, User
from app.schemas.scheduling import (
    CentreClosureCreate,
    CentreClosureRead,
    OccurrenceQuery,
    OccurrenceRead,
    SessionOccurrenceExceptionCreate,
    SessionOccurrenceExceptionRead,
    StudentAbsenceCreate,
    StudentAbsenceRead,
    TeacherLeaveCreate,
    TeacherLeaveRead,
)
from app.services.access import (
    AccessScope,
    apply_student_absence_scope,
    apply_teacher_leave_scope,
    enforce_occurrence_filters,
    ensure_student_access,
    ensure_teacher_access,
    get_session_or_404,
    get_student_absence_or_404,
    get_teacher_leave_or_404,
)
from app.services.audit import write_audit_log
from app.services.scheduling import build_occurrences, validate_occurrence_exception


router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/occurrences/query", response_model=list[OccurrenceRead])
def query_occurrences(
    payload: OccurrenceQuery,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[OccurrenceRead]:
    teacher_id, student_id = enforce_occurrence_filters(
        db,
        scope,
        teacher_id=payload.teacher_id,
        student_id=payload.student_id,
    )
    return build_occurrences(
        db,
        date_from=payload.date_from,
        date_to=payload.date_to,
        teacher_id=teacher_id,
        student_id=student_id,
    )


@router.post("/sessions/{session_id}/exceptions", response_model=SessionOccurrenceExceptionRead, status_code=status.HTTP_201_CREATED)
def save_occurrence_exception(
    session_id: int,
    payload: SessionOccurrenceExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> SessionOccurrenceException:
    session = get_session_or_404(db, scope, session_id)
    errors = validate_occurrence_exception(db, session=session, occurrence_date=payload.occurrence_date, payload=payload)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    record = db.scalar(
        select(SessionOccurrenceException).where(
            SessionOccurrenceException.session_id == session_id,
            SessionOccurrenceException.occurrence_date == payload.occurrence_date,
        )
    )
    if record is None:
        record = SessionOccurrenceException(
            session_id=session_id,
            occurrence_date=payload.occurrence_date,
            changed_by_user_id=current_user.id,
            **payload.model_dump(exclude={"occurrence_date"}),
        )
        db.add(record)
    else:
        for key, value in payload.model_dump(exclude={"occurrence_date"}).items():
            setattr(record, key, value)
        record.changed_by_user_id = current_user.id
        db.add(record)

    write_audit_log(
        db,
        action="schedule.exception.saved",
        entity_type="session_occurrence_exception",
        entity_id=f"{session_id}:{payload.occurrence_date.isoformat()}",
        summary=f"Occurrence exception saved with status {payload.status}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(record)
    return record


@router.delete("/sessions/{session_id}/exceptions/{occurrence_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_occurrence_exception(
    session_id: int,
    occurrence_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> None:
    get_session_or_404(db, scope, session_id)
    record = db.scalar(
        select(SessionOccurrenceException).where(
            SessionOccurrenceException.session_id == session_id,
            SessionOccurrenceException.occurrence_date == occurrence_date,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Occurrence exception not found")
    write_audit_log(
        db,
        action="schedule.exception.deleted",
        entity_type="session_occurrence_exception",
        entity_id=f"{session_id}:{occurrence_date.isoformat()}",
        summary="Occurrence exception deleted",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(record)
    db.commit()


@router.get("/closures", response_model=list[CentreClosureRead])
def list_closures(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> list[CentreClosure]:
    return list(db.scalars(select(CentreClosure).order_by(CentreClosure.start_date)))


@router.post("/closures", response_model=CentreClosureRead, status_code=status.HTTP_201_CREATED)
def create_closure(
    payload: CentreClosureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> CentreClosure:
    closure = CentreClosure(**payload.model_dump())
    db.add(closure)
    db.flush()
    write_audit_log(
        db,
        action="schedule.closure.created",
        entity_type="centre_closure",
        entity_id=str(closure.id),
        summary=f"Closure created: {payload.name}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(closure)
    return closure


@router.delete("/closures/{closure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_closure(
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    closure = db.get(CentreClosure, closure_id)
    if closure is None:
        raise HTTPException(status_code=404, detail="Closure not found")
    write_audit_log(
        db,
        action="schedule.closure.deleted",
        entity_type="centre_closure",
        entity_id=str(closure.id),
        summary="Closure deleted",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(closure)
    db.commit()


@router.get("/teacher-leave", response_model=list[TeacherLeaveRead])
def list_teacher_leave(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[TeacherLeave]:
    return list(db.scalars(apply_teacher_leave_scope(select(TeacherLeave), scope).order_by(TeacherLeave.start_date)))


@router.post("/teacher-leave", response_model=TeacherLeaveRead, status_code=status.HTTP_201_CREATED)
def create_teacher_leave(
    payload: TeacherLeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> TeacherLeave:
    ensure_teacher_access(scope, payload.teacher_id)
    leave = TeacherLeave(**payload.model_dump())
    db.add(leave)
    db.flush()
    write_audit_log(
        db,
        action="schedule.teacher_leave.created",
        entity_type="teacher_leave",
        entity_id=str(leave.id),
        summary="Teacher leave created",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(leave)
    return leave


@router.delete("/teacher-leave/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> None:
    leave = get_teacher_leave_or_404(db, scope, leave_id)
    write_audit_log(
        db,
        action="schedule.teacher_leave.deleted",
        entity_type="teacher_leave",
        entity_id=str(leave.id),
        summary="Teacher leave deleted",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(leave)
    db.commit()


@router.get("/student-absences", response_model=list[StudentAbsenceRead])
def list_student_absences(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[StudentAbsence]:
    return list(
        db.scalars(apply_student_absence_scope(select(StudentAbsence), scope).order_by(StudentAbsence.start_date))
    )


@router.post("/student-absences", response_model=StudentAbsenceRead, status_code=status.HTTP_201_CREATED)
def create_student_absence(
    payload: StudentAbsenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> StudentAbsence:
    ensure_student_access(db, scope, payload.student_id)
    absence = StudentAbsence(**payload.model_dump())
    db.add(absence)
    db.flush()
    write_audit_log(
        db,
        action="schedule.student_absence.created",
        entity_type="student_absence",
        entity_id=str(absence.id),
        summary="Student absence created",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(absence)
    return absence


@router.delete("/student-absences/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_absence(
    absence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> None:
    absence = get_student_absence_or_404(db, scope, absence_id)
    write_audit_log(
        db,
        action="schedule.student_absence.deleted",
        entity_type="student_absence",
        entity_id=str(absence.id),
        summary="Student absence deleted",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(absence)
    db.commit()
