from collections import defaultdict
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import CentreClosure, Session as SessionModel, SessionOccurrenceException, StudentAbsence, TeacherLeave
from app.schemas.scheduling import OccurrenceRead, SessionOccurrenceExceptionCreate
from app.services.time_utils import daterange, ranges_overlap


def _block_matches(block, occurrence_date: date, start_minute: int, end_minute: int) -> bool:
    if occurrence_date < block.start_date or occurrence_date > block.end_date:
        return False
    if block.start_minute is None or block.end_minute is None:
        return True
    return ranges_overlap(start_minute, end_minute, block.start_minute, block.end_minute)


def build_occurrences(
    db: Session,
    *,
    date_from: date,
    date_to: date,
    teacher_id: int | None = None,
    student_id: int | None = None,
) -> list[OccurrenceRead]:
    query = select(SessionModel).where(SessionModel.status == "active")
    if teacher_id is not None:
        query = query.where(SessionModel.teacher_id == teacher_id)
    if student_id is not None:
        query = query.where(SessionModel.student_id == student_id)
    sessions = list(db.scalars(query.order_by(SessionModel.weekday, SessionModel.start_minute)))
    if not sessions:
        return []

    session_ids = [session.id for session in sessions]
    exceptions = list(
        db.scalars(
            select(SessionOccurrenceException).where(
                SessionOccurrenceException.session_id.in_(session_ids),
                or_(
                    SessionOccurrenceException.occurrence_date.between(date_from, date_to),
                    SessionOccurrenceException.rescheduled_date.between(date_from, date_to),
                ),
            )
        )
    )
    exception_map = {(item.session_id, item.occurrence_date): item for item in exceptions}
    closures_by_date = defaultdict(list)
    for closure in db.scalars(select(CentreClosure).where(CentreClosure.start_date <= date_to, CentreClosure.end_date >= date_from)):
        for occurrence_date in daterange(max(closure.start_date, date_from), min(closure.end_date, date_to)):
            closures_by_date[occurrence_date].append(closure)

    teacher_leave = list(db.scalars(select(TeacherLeave).where(TeacherLeave.start_date <= date_to, TeacherLeave.end_date >= date_from)))
    student_absences = list(
        db.scalars(select(StudentAbsence).where(StudentAbsence.start_date <= date_to, StudentAbsence.end_date >= date_from))
    )

    def build_occurrence(session: SessionModel, occurrence_date: date, exception: SessionOccurrenceException | None) -> OccurrenceRead:
        status = "scheduled"
        impact_reasons: list[str] = []
        effective_date = occurrence_date
        start_minute = session.start_minute
        end_minute = session.end_minute
        notes = session.notes or ""

        if exception is not None:
            status = exception.status
            notes = exception.notes or notes
            if exception.status == "rescheduled":
                effective_date = exception.rescheduled_date or occurrence_date
                start_minute = exception.rescheduled_start_minute or session.start_minute
                end_minute = exception.rescheduled_end_minute or session.end_minute

        if closures_by_date.get(occurrence_date):
            impact_reasons.append("Centre closure or holiday")
            if exception is None:
                status = "holiday_affected"

        if effective_date != occurrence_date and closures_by_date.get(effective_date):
            impact_reasons.append("Centre closure or holiday on rescheduled date")

        if any(
            block.teacher_id == session.teacher_id and _block_matches(block, effective_date, start_minute, end_minute)
            for block in teacher_leave
        ):
            impact_reasons.append("Teacher leave blocks this occurrence")

        if any(
            block.student_id == session.student_id and _block_matches(block, effective_date, start_minute, end_minute)
            for block in student_absences
        ):
            impact_reasons.append("Student absence blocks this occurrence")

        return OccurrenceRead(
            session_id=session.id,
            occurrence_date=occurrence_date,
            weekday=session.weekday,
            effective_date=effective_date,
            start_minute=start_minute,
            end_minute=end_minute,
            teacher_id=session.teacher_id,
            student_id=session.student_id,
            subject=session.subject,
            base_status=session.status,
            occurrence_status=status,
            impact_reasons=impact_reasons,
            notes=notes,
        )

    occurrences: list[OccurrenceRead] = []
    for session in sessions:
        session_end = session.end_date or date_to
        active_start = max(session.start_date, date_from)
        active_end = min(session_end, date_to)
        if active_start > active_end:
            continue

        for occurrence_date in daterange(active_start, active_end):
            if occurrence_date.weekday() != session.weekday:
                continue
            exception = exception_map.get((session.id, occurrence_date))
            occurrences.append(build_occurrence(session, occurrence_date, exception))

        for exception in exceptions:
            if exception.session_id != session.id or exception.status != "rescheduled" or exception.rescheduled_date is None:
                continue
            if exception.rescheduled_date < date_from or exception.rescheduled_date > date_to:
                continue
            if date_from <= exception.occurrence_date <= date_to:
                continue
            occurrences.append(build_occurrence(session, exception.occurrence_date, exception))

    return sorted(occurrences, key=lambda item: (item.effective_date, item.start_minute, item.teacher_id, item.student_id))


def validate_occurrence_exception(
    db: Session,
    *,
    session: SessionModel,
    occurrence_date: date,
    payload: SessionOccurrenceExceptionCreate,
) -> list[str]:
    if payload.status != "rescheduled":
        return []

    assert payload.rescheduled_date is not None
    assert payload.rescheduled_start_minute is not None
    assert payload.rescheduled_end_minute is not None

    errors: list[str] = []
    target_date = payload.rescheduled_date
    target_start = payload.rescheduled_start_minute
    target_end = payload.rescheduled_end_minute

    if any(
        _block_matches(block, target_date, target_start, target_end)
        for block in db.scalars(
            select(CentreClosure).where(CentreClosure.start_date <= target_date, CentreClosure.end_date >= target_date)
        )
    ):
        errors.append("Rescheduled occurrence falls inside a centre closure or holiday.")

    if any(
        block.teacher_id == session.teacher_id and _block_matches(block, target_date, target_start, target_end)
        for block in db.scalars(
            select(TeacherLeave).where(
                TeacherLeave.teacher_id == session.teacher_id,
                TeacherLeave.start_date <= target_date,
                TeacherLeave.end_date >= target_date,
            )
        )
    ):
        errors.append("Teacher leave blocks the rescheduled occurrence.")

    if any(
        block.student_id == session.student_id and _block_matches(block, target_date, target_start, target_end)
        for block in db.scalars(
            select(StudentAbsence).where(
                StudentAbsence.student_id == session.student_id,
                StudentAbsence.start_date <= target_date,
                StudentAbsence.end_date >= target_date,
            )
        )
    ):
        errors.append("Student absence blocks the rescheduled occurrence.")

    teacher_occurrences = build_occurrences(
        db,
        date_from=target_date,
        date_to=target_date,
        teacher_id=session.teacher_id,
    )
    student_occurrences = build_occurrences(
        db,
        date_from=target_date,
        date_to=target_date,
        student_id=session.student_id,
    )

    seen: set[tuple[int, date]] = set()
    for occurrence in teacher_occurrences + student_occurrences:
        occurrence_key = (occurrence.session_id, occurrence.occurrence_date)
        if occurrence_key in seen:
            continue
        seen.add(occurrence_key)

        if occurrence.session_id == session.id and occurrence.occurrence_date == occurrence_date:
            continue
        if occurrence.occurrence_status == "cancelled":
            continue
        if occurrence.effective_date != target_date:
            continue
        if ranges_overlap(target_start, target_end, occurrence.start_minute, occurrence.end_minute):
            errors.append("Rescheduled occurrence conflicts with another scheduled lesson.")
            break

    return errors
