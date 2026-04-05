import sqlite3
import sys
from datetime import date
from pathlib import Path

from app.core.db import SessionLocal
from app.models import AvailabilitySlot, Session, Student, StudentBlockedTime, StudentPreference, Teacher


def _require_row_value(row: sqlite3.Row, key: str):
    try:
        return row[key]
    except IndexError as exc:
        raise ValueError(f"Legacy database is missing required column: {key}") from exc


def _require_mapped_id(mapping: dict[int, int], legacy_id: int, entity_name: str) -> int:
    mapped_id = mapping.get(legacy_id)
    if mapped_id is None:
        raise ValueError(f"Legacy {entity_name} id {legacy_id} references a record that was not imported")
    return mapped_id


def import_legacy_sqlite(sqlite_path: str) -> None:
    source = Path(sqlite_path)
    if not source.exists():
        raise FileNotFoundError(f"Legacy SQLite database not found: {source}")

    connection = sqlite3.connect(source)
    connection.row_factory = sqlite3.Row
    db = SessionLocal()
    try:
        teacher_id_map: dict[int, int] = {}
        student_id_map: dict[int, int] = {}

        for row in connection.execute("SELECT * FROM teachers ORDER BY id"):
            teacher = Teacher(
                full_name=_require_row_value(row, "full_name"),
                email=_require_row_value(row, "email"),
                subject_tags=row["subject_tags"] or "",
                active=bool(row["active"]),
                notes="Imported from legacy SQLite",
            )
            db.add(teacher)
            db.flush()
            teacher_id_map[row["id"]] = teacher.id

        for row in connection.execute("SELECT * FROM students ORDER BY id"):
            student = Student(
                full_name=_require_row_value(row, "full_name"),
                parent_name=row["parent_name"] or "",
                contact_email=_require_row_value(row, "contact_email"),
                active=bool(row["active"]),
                notes=row["notes"] or "",
            )
            db.add(student)
            db.flush()
            student_id_map[row["id"]] = student.id

        for row in connection.execute("SELECT * FROM availability_slots ORDER BY id"):
            db.add(
                AvailabilitySlot(
                    teacher_id=_require_mapped_id(teacher_id_map, row["teacher_id"], "teacher"),
                    weekday=row["weekday"],
                    start_minute=row["start_minute"],
                    end_minute=row["end_minute"],
                )
            )

        for row in connection.execute("SELECT * FROM student_preferences ORDER BY id"):
            db.add(
                StudentPreference(
                    student_id=_require_mapped_id(student_id_map, row["student_id"], "student"),
                    weekday=row["weekday"],
                    start_minute=row["start_minute"],
                    end_minute=row["end_minute"],
                    priority=row["priority"],
                )
            )

        for row in connection.execute("SELECT * FROM student_blocked_times ORDER BY id"):
            db.add(
                StudentBlockedTime(
                    student_id=_require_mapped_id(student_id_map, row["student_id"], "student"),
                    weekday=row["weekday"],
                    start_minute=row["start_minute"],
                    end_minute=row["end_minute"],
                    reason=row["reason"] or "",
                )
            )

        for row in connection.execute("SELECT * FROM sessions ORDER BY id"):
            db.add(
                Session(
                    teacher_id=_require_mapped_id(teacher_id_map, row["teacher_id"], "teacher"),
                    student_id=_require_mapped_id(student_id_map, row["student_id"], "student"),
                    weekday=row["weekday"],
                    start_minute=row["start_minute"],
                    end_minute=row["end_minute"],
                    duration_minutes=row["duration_minutes"],
                    subject=row["subject"] or "",
                    status="active" if row["status"] == "active" else "inactive",
                    start_date=date.fromisoformat(_require_row_value(row, "start_date")),
                    end_date=date.fromisoformat(row["end_date"]) if row["end_date"] else None,
                    notes=row["notes"] or "Imported from legacy SQLite",
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: py -m app.import_legacy_sqlite <path-to-legacy-sqlite-db>")
    import_legacy_sqlite(sys.argv[1])
