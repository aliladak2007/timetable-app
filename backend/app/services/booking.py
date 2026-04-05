from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Session as SessionModel
from app.models import Student, StudentBlockedTime, Teacher
from app.schemas.session import SessionCreate
from app.services.time_utils import contains_range, ranges_overlap, session_is_active_on_date_range


def validate_session_booking(db: Session, payload: SessionCreate, existing_session_id: int | None = None) -> list[str]:
    errors: list[str] = []
    teacher = db.get(Teacher, payload.teacher_id)
    if teacher is None or not teacher.active:
        return ["Teacher is not available for booking."]
    student = db.get(Student, payload.student_id)
    if student is None or not student.active:
        return ["Student is not available for booking."]

    availability_matches = [
        slot
        for slot in teacher.availability_slots
        if slot.weekday == payload.weekday
        and contains_range(slot.start_minute, slot.end_minute, payload.start_minute, payload.end_minute)
    ]
    if not availability_matches:
        errors.append("Session must fit inside teacher availability.")

    teacher_sessions = list(
        db.scalars(select(SessionModel).where(SessionModel.teacher_id == payload.teacher_id, SessionModel.status == "active"))
    )
    student_sessions = list(
        db.scalars(select(SessionModel).where(SessionModel.student_id == payload.student_id, SessionModel.status == "active"))
    )
    active_date = payload.start_date
    for session in teacher_sessions:
        if existing_session_id is not None and session.id == existing_session_id:
            continue
        if not session_is_active_on_date_range(session.start_date, session.end_date, active_date, payload.end_date):
            continue
        if session.weekday == payload.weekday and ranges_overlap(
            payload.start_minute,
            payload.end_minute,
            session.start_minute,
            session.end_minute,
        ):
            errors.append("Teacher already has a recurring session in that slot.")
            break

    for session in student_sessions:
        if existing_session_id is not None and session.id == existing_session_id:
            continue
        if not session_is_active_on_date_range(session.start_date, session.end_date, active_date, payload.end_date):
            continue
        if session.weekday == payload.weekday and ranges_overlap(
            payload.start_minute,
            payload.end_minute,
            session.start_minute,
            session.end_minute,
        ):
            errors.append("Student already has a recurring session in that slot.")
            break

    blocked_times = list(db.scalars(select(StudentBlockedTime).where(StudentBlockedTime.student_id == payload.student_id)))
    for blocked in blocked_times:
        if blocked.weekday == payload.weekday and ranges_overlap(
            payload.start_minute,
            payload.end_minute,
            blocked.start_minute,
            blocked.end_minute,
        ):
            errors.append("Student is blocked during that slot.")
            break

    return errors
