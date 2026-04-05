from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import AvailabilitySlot, Session as SessionModel, Student, StudentBlockedTime, StudentPreference, Teacher
from app.models.base import Base
from app.schemas.matching import MatchSuggestionRequest
from app.services.matching import suggest_slots


def build_db() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    return local_session()


def seed_matching_case(db: Session) -> tuple[int, int]:
    teacher = Teacher(full_name="Aisha Khan", email="aisha@test.com", subject_tags="Maths")
    student = Student(full_name="Sam Green", parent_name="Parent", contact_email="sam@test.com")
    db.add_all([teacher, student])
    db.flush()

    db.add_all(
        [
            AvailabilitySlot(teacher_id=teacher.id, weekday=0, start_minute=900, end_minute=1080),
            StudentPreference(student_id=student.id, weekday=0, start_minute=900, end_minute=1080, priority=1),
            StudentBlockedTime(student_id=student.id, weekday=0, start_minute=960, end_minute=1020, reason="Club"),
            SessionModel(
                teacher_id=teacher.id,
                student_id=student.id,
                weekday=0,
                start_minute=1020,
                end_minute=1080,
                duration_minutes=60,
                subject="Maths",
                status="active",
                start_date=date(2026, 1, 1),
            ),
        ]
    )
    other_student = Student(full_name="Other Learner", parent_name="Parent", contact_email="other@test.com")
    db.add(other_student)
    db.flush()
    db.add(
        SessionModel(
            teacher_id=teacher.id,
            student_id=other_student.id,
            weekday=0,
            start_minute=930,
            end_minute=990,
            duration_minutes=60,
            subject="Maths",
            status="active",
            start_date=date(2026, 1, 1),
        )
    )
    db.commit()
    return teacher.id, student.id


def test_matching_filters_conflicts_and_blocked_times() -> None:
    db = build_db()
    teacher_id, student_id = seed_matching_case(db)

    suggestions, rejected_slots = suggest_slots(
        db,
        MatchSuggestionRequest(
            teacher_id=teacher_id,
            student_id=student_id,
            duration_minutes=60,
            start_date=date(2026, 2, 1),
        ),
    )

    returned_slots = {(item.start_minute, item.end_minute) for item in suggestions}
    assert (900, 960) not in returned_slots
    assert (945, 1005) not in returned_slots
    assert (960, 1020) not in returned_slots
    assert rejected_slots


def test_matching_ranking_prefers_earlier_slot_when_otherwise_equal() -> None:
    db = build_db()
    teacher = Teacher(full_name="Daniel Reed", email="daniel@test.com", subject_tags="English")
    student = Student(full_name="Eva Hart", parent_name="Parent", contact_email="eva@test.com")
    db.add_all([teacher, student])
    db.flush()
    db.add_all(
        [
            AvailabilitySlot(teacher_id=teacher.id, weekday=1, start_minute=900, end_minute=1080),
            StudentPreference(student_id=student.id, weekday=1, start_minute=900, end_minute=1080, priority=1),
        ]
    )
    db.commit()

    suggestions, _ = suggest_slots(
        db,
        MatchSuggestionRequest(teacher_id=teacher.id, student_id=student.id, duration_minutes=60),
    )

    assert suggestions[0].start_minute == 900
    assert suggestions[0].score >= suggestions[-1].score


def test_matching_returns_empty_when_no_preferences_are_available() -> None:
    db = build_db()
    teacher = Teacher(full_name="No Pref Teacher", email="nopref@test.com", subject_tags="Science")
    student = Student(full_name="No Pref Student", parent_name="Parent", contact_email="nopref-student@test.com")
    db.add_all([teacher, student])
    db.flush()
    db.add(AvailabilitySlot(teacher_id=teacher.id, weekday=2, start_minute=900, end_minute=1020))
    db.commit()

    suggestions, _ = suggest_slots(
        db,
        MatchSuggestionRequest(teacher_id=teacher.id, student_id=student.id, duration_minutes=60),
    )

    assert suggestions == []
