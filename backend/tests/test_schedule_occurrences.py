from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import CentreClosure, Session, SessionOccurrenceException, Student, Teacher
from app.models.base import Base
from app.services.scheduling import build_occurrences


def test_closure_and_reschedule_are_applied_to_occurrences() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    db = local_session()

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
    db.add(CentreClosure(name="Bank Holiday", closure_type="holiday", start_date=date(2026, 1, 5), end_date=date(2026, 1, 5)))
    db.add(
        SessionOccurrenceException(
            session_id=session.id,
            occurrence_date=date(2026, 1, 12),
            status="rescheduled",
            rescheduled_date=date(2026, 1, 13),
            rescheduled_start_minute=960,
            rescheduled_end_minute=1020,
            notes="Moved by admin",
        )
    )
    db.commit()

    occurrences = build_occurrences(db, date_from=date(2026, 1, 5), date_to=date(2026, 1, 13))
    assert any(item.occurrence_status == "holiday_affected" for item in occurrences)
    assert any(item.occurrence_status == "rescheduled" and item.effective_date == date(2026, 1, 13) for item in occurrences)
