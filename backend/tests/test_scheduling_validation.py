from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import CentreClosure, Session, SessionOccurrenceException, Student, StudentAbsence, Teacher, TeacherLeave
from app.models.base import Base
from app.schemas.scheduling import OccurrenceQuery, SessionOccurrenceExceptionCreate
from app.services.scheduling import build_occurrences, validate_occurrence_exception


def build_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    return local_session()


def test_occurrence_query_rejects_inverted_date_range() -> None:
    with pytest.raises(ValueError, match="date_to cannot be before date_from"):
        OccurrenceQuery.model_validate({"date_from": "2026-02-01", "date_to": "2026-01-01"})


def test_rescheduled_exception_requires_complete_fields() -> None:
    with pytest.raises(ValueError, match="Rescheduled occurrences require date, start minute, and end minute"):
        SessionOccurrenceExceptionCreate.model_validate(
            {"occurrence_date": "2026-01-05", "status": "rescheduled", "rescheduled_date": "2026-01-06"}
        )


def test_build_occurrences_applies_blocks_on_rescheduled_date() -> None:
    db = build_db()
    teacher = Teacher(full_name="Teacher", email="teacher@test.com", subject_tags="Maths")
    student = Student(full_name="Student", parent_name="Parent", contact_email="student@test.com")
    db.add_all([teacher, student])
    db.flush()

    session = Session(
        teacher_id=teacher.id,
        student_id=student.id,
        weekday=0,
        start_minute=900,
        end_minute=960,
        duration_minutes=60,
        subject="Maths",
        status="active",
        start_date=date(2026, 1, 1),
    )
    db.add(session)
    db.flush()
    db.add(
        SessionOccurrenceException(
            session_id=session.id,
            occurrence_date=date(2026, 1, 5),
            status="rescheduled",
            rescheduled_date=date(2026, 1, 6),
            rescheduled_start_minute=900,
            rescheduled_end_minute=960,
        )
    )
    db.add(TeacherLeave(teacher_id=teacher.id, start_date=date(2026, 1, 6), end_date=date(2026, 1, 6), reason="Leave"))
    db.add(StudentAbsence(student_id=student.id, start_date=date(2026, 1, 6), end_date=date(2026, 1, 6), reason="Absent"))
    db.add(CentreClosure(name="Closure", closure_type="closure", start_date=date(2026, 1, 6), end_date=date(2026, 1, 6)))
    db.commit()

    occurrences = build_occurrences(db, date_from=date(2026, 1, 5), date_to=date(2026, 1, 6))

    rescheduled = next(item for item in occurrences if item.occurrence_status == "rescheduled")
    assert rescheduled.effective_date == date(2026, 1, 6)
    assert "Teacher leave blocks this occurrence" in rescheduled.impact_reasons
    assert "Student absence blocks this occurrence" in rescheduled.impact_reasons
    assert "Centre closure or holiday on rescheduled date" in rescheduled.impact_reasons


def test_build_occurrences_includes_reschedules_from_outside_requested_range() -> None:
    db = build_db()
    teacher = Teacher(full_name="Teacher", email="teacher@test.com", subject_tags="Maths")
    student = Student(full_name="Student", parent_name="Parent", contact_email="student@test.com")
    db.add_all([teacher, student])
    db.flush()

    session = Session(
        teacher_id=teacher.id,
        student_id=student.id,
        weekday=0,
        start_minute=900,
        end_minute=960,
        duration_minutes=60,
        subject="Maths",
        status="active",
        start_date=date(2026, 1, 1),
    )
    db.add(session)
    db.flush()
    db.add(
        SessionOccurrenceException(
            session_id=session.id,
            occurrence_date=date(2026, 1, 5),
            status="rescheduled",
            rescheduled_date=date(2026, 1, 6),
            rescheduled_start_minute=900,
            rescheduled_end_minute=960,
        )
    )
    db.commit()

    occurrences = build_occurrences(db, date_from=date(2026, 1, 6), date_to=date(2026, 1, 6))

    assert len(occurrences) == 1
    assert occurrences[0].occurrence_status == "rescheduled"
    assert occurrences[0].occurrence_date == date(2026, 1, 5)
    assert occurrences[0].effective_date == date(2026, 1, 6)


def test_rescheduled_exception_rejects_conflicting_slot() -> None:
    db = build_db()
    teacher = Teacher(full_name="Teacher", email="teacher@test.com", subject_tags="Maths")
    student_one = Student(full_name="Student One", parent_name="Parent", contact_email="student-one@test.com")
    student_two = Student(full_name="Student Two", parent_name="Parent", contact_email="student-two@test.com")
    db.add_all([teacher, student_one, student_two])
    db.flush()

    base_session = Session(
        teacher_id=teacher.id,
        student_id=student_one.id,
        weekday=0,
        start_minute=900,
        end_minute=960,
        duration_minutes=60,
        subject="Maths",
        status="active",
        start_date=date(2026, 1, 1),
    )
    conflicting_session = Session(
        teacher_id=teacher.id,
        student_id=student_two.id,
        weekday=1,
        start_minute=900,
        end_minute=960,
        duration_minutes=60,
        subject="Science",
        status="active",
        start_date=date(2026, 1, 1),
    )
    db.add_all([base_session, conflicting_session])
    db.commit()

    payload = SessionOccurrenceExceptionCreate.model_validate(
        {
            "occurrence_date": "2026-01-05",
            "status": "rescheduled",
            "rescheduled_date": "2026-01-06",
            "rescheduled_start_minute": 900,
            "rescheduled_end_minute": 960,
        }
    )

    errors = validate_occurrence_exception(db, session=base_session, occurrence_date=date(2026, 1, 5), payload=payload)

    assert "Rescheduled occurrence conflicts with another scheduled lesson." in errors
