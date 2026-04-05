import os
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import app.core.config as config_module
from app.import_legacy_sqlite import import_legacy_sqlite
from app.core.db import engine
from app.models.base import Base
from app.schemas.scheduling import OccurrenceRead
from app.services.calendar import build_ics_calendar


def test_ics_calendar_uses_configured_timezone() -> None:
    calendar_bytes = build_ics_calendar(
        "Teacher Calendar",
        [
            OccurrenceRead(
                session_id=1,
                occurrence_date="2026-07-06",
                weekday=0,
                effective_date="2026-07-06",
                start_minute=540,
                end_minute=600,
                teacher_id=1,
                student_id=1,
                subject="Maths",
                base_status="active",
                occurrence_status="scheduled",
            )
        ],
    )

    calendar_text = calendar_bytes.decode("utf-8")
    assert "TZID=Europe/London" in calendar_text
    assert "DTSTART:20260706T090000Z" not in calendar_text


def test_desktop_settings_default_to_local_sqlite_and_auto_schema() -> None:
    with TemporaryDirectory() as temp_dir:
        os.environ["TIMETABLING_APP_ENV"] = "desktop"
        os.environ["TIMETABLING_CONFIG_DIR"] = temp_dir
        os.environ.pop("TIMETABLING_DATABASE_URL", None)
        os.environ.pop("TIMETABLING_DATABASE_URL_FILE", None)
        config_module.get_settings.cache_clear()
        settings = config_module.get_settings()

        assert settings.auto_create_schema is True
        assert settings.resolved_database_url.startswith("sqlite:///")
        assert Path(settings.resolved_database_url.removeprefix("sqlite:///")).name == "timetabling.db"

    config_module.get_settings.cache_clear()


def test_legacy_import_raises_clear_error_for_orphaned_references() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        with TemporaryDirectory() as temp_dir:
            sqlite_path = Path(temp_dir) / "legacy.db"
            connection = sqlite3.connect(sqlite_path)
            try:
                connection.executescript(
                    """
                    CREATE TABLE teachers (id INTEGER PRIMARY KEY, full_name TEXT, email TEXT, subject_tags TEXT, active INTEGER);
                    CREATE TABLE students (id INTEGER PRIMARY KEY, full_name TEXT, parent_name TEXT, contact_email TEXT, active INTEGER, notes TEXT);
                    CREATE TABLE availability_slots (id INTEGER PRIMARY KEY, teacher_id INTEGER, weekday INTEGER, start_minute INTEGER, end_minute INTEGER);
                    CREATE TABLE student_preferences (id INTEGER PRIMARY KEY, student_id INTEGER, weekday INTEGER, start_minute INTEGER, end_minute INTEGER, priority INTEGER);
                    CREATE TABLE student_blocked_times (id INTEGER PRIMARY KEY, student_id INTEGER, weekday INTEGER, start_minute INTEGER, end_minute INTEGER, reason TEXT);
                    CREATE TABLE sessions (
                      id INTEGER PRIMARY KEY,
                      teacher_id INTEGER,
                      student_id INTEGER,
                      weekday INTEGER,
                      start_minute INTEGER,
                      end_minute INTEGER,
                      duration_minutes INTEGER,
                      subject TEXT,
                      status TEXT,
                      start_date TEXT,
                      end_date TEXT,
                      notes TEXT
                    );
                    INSERT INTO teachers VALUES (1, 'Teacher', 'teacher@test.com', 'Maths', 1);
                    INSERT INTO students VALUES (1, 'Student', 'Parent', 'student@test.com', 1, '');
                    INSERT INTO sessions VALUES (1, 999, 1, 0, 900, 960, 60, 'Maths', 'active', '2026-01-01', NULL, '');
                    """
                )
                connection.commit()
            finally:
                connection.close()

            with pytest.raises(ValueError, match="Legacy teacher id 999 references a record that was not imported"):
                import_legacy_sqlite(str(sqlite_path))
    finally:
        Base.metadata.drop_all(bind=engine)
