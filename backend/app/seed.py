from datetime import date

from app.core.db import SessionLocal, engine
from app.models import AvailabilitySlot, Session, Student, StudentBlockedTime, StudentPreference, Teacher
from app.models.base import Base


def seed() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        teachers = [
            Teacher(full_name="Aisha Khan", email="aisha@example.com", subject_tags="Maths,Physics"),
            Teacher(full_name="Daniel Reed", email="daniel@example.com", subject_tags="English,History"),
            Teacher(full_name="Priya Shah", email="priya@example.com", subject_tags="Chemistry,Biology"),
        ]
        db.add_all(teachers)
        db.flush()

        db.add_all(
            [
                AvailabilitySlot(teacher_id=teachers[0].id, weekday=0, start_minute=900, end_minute=1140),
                AvailabilitySlot(teacher_id=teachers[0].id, weekday=2, start_minute=840, end_minute=1080),
                AvailabilitySlot(teacher_id=teachers[0].id, weekday=4, start_minute=900, end_minute=1200),
                AvailabilitySlot(teacher_id=teachers[1].id, weekday=1, start_minute=930, end_minute=1170),
                AvailabilitySlot(teacher_id=teachers[1].id, weekday=3, start_minute=870, end_minute=1110),
                AvailabilitySlot(teacher_id=teachers[2].id, weekday=0, start_minute=780, end_minute=1020),
            ]
        )

        students = [
            Student(full_name="Amelia Stone", parent_name="Rachel Stone", contact_email="amelia@example.com"),
            Student(full_name="Bilal Hussain", parent_name="Samina Hussain", contact_email="bilal@example.com"),
            Student(full_name="Chloe Turner", parent_name="Mark Turner", contact_email="chloe@example.com"),
        ]
        db.add_all(students)
        db.flush()

        db.add_all(
            [
                StudentPreference(student_id=students[0].id, weekday=0, start_minute=930, end_minute=1080, priority=1),
                StudentPreference(student_id=students[1].id, weekday=2, start_minute=900, end_minute=1050, priority=1),
                StudentPreference(student_id=students[2].id, weekday=1, start_minute=960, end_minute=1140, priority=1),
            ]
        )
        db.add_all(
            [
                StudentBlockedTime(student_id=students[0].id, weekday=0, start_minute=990, end_minute=1050, reason="Sports club"),
                StudentBlockedTime(student_id=students[1].id, weekday=2, start_minute=960, end_minute=1020, reason="School pickup"),
            ]
        )

        db.add_all(
            [
                Session(
                    teacher_id=teachers[0].id,
                    student_id=students[0].id,
                    weekday=0,
                    start_minute=900,
                    end_minute=960,
                    duration_minutes=60,
                    subject="Maths",
                    status="active",
                    start_date=date(2026, 1, 12),
                ),
                Session(
                    teacher_id=teachers[1].id,
                    student_id=students[2].id,
                    weekday=1,
                    start_minute=1020,
                    end_minute=1080,
                    duration_minutes=60,
                    subject="English",
                    status="active",
                    start_date=date(2026, 1, 13),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
