from datetime import date

from pydantic import field_validator

from app.schemas.common import ORMModel, TimestampedRead


class SessionCreate(ORMModel):
    teacher_id: int
    student_id: int
    weekday: int
    start_minute: int
    end_minute: int
    duration_minutes: int
    subject: str = ""
    status: str = "active"
    start_date: date
    end_date: date | None = None
    notes: str = ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        return value

    @field_validator("weekday")
    @classmethod
    def validate_weekday(cls, value: int) -> int:
        if value < 0 or value > 6:
            raise ValueError("weekday must be between 0 and 6")
        return value

    @field_validator("start_minute", "end_minute")
    @classmethod
    def validate_minutes(cls, value: int) -> int:
        if value < 0 or value > 1440:
            raise ValueError("minute values must be between 0 and 1440")
        if value % 15 != 0:
            raise ValueError("minute values must be in 15-minute increments")
        return value

    @field_validator("end_minute")
    @classmethod
    def validate_time_order(cls, value: int, info) -> int:
        start_minute = info.data.get("start_minute")
        if start_minute is not None and value <= start_minute:
            raise ValueError("end_minute must be greater than start_minute")
        return value

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, value: int, info) -> int:
        start_minute = info.data.get("start_minute")
        end_minute = info.data.get("end_minute")
        if start_minute is not None and end_minute is not None and value != end_minute - start_minute:
            raise ValueError("duration_minutes must match the time range")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, value: date | None, info) -> date | None:
        start_date = info.data.get("start_date")
        if value is not None and start_date is not None and value < start_date:
            raise ValueError("end_date cannot be before start_date")
        return value


class SessionUpdate(ORMModel):
    subject: str | None = None
    status: str | None = None
    end_date: date | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        return value


class SessionRead(TimestampedRead, SessionCreate):
    id: int
    created_by_user_id: int | None = None
