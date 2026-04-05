from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import DatedWindowBase, ORMModel, TimestampedRead


class SessionOccurrenceExceptionCreate(BaseModel):
    occurrence_date: date
    status: str
    rescheduled_date: date | None = None
    rescheduled_start_minute: int | None = None
    rescheduled_end_minute: int | None = None
    notes: str = ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"cancelled", "completed", "rescheduled", "missed", "holiday_affected"}
        if value not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("rescheduled_end_minute")
    @classmethod
    def validate_rescheduled_time(cls, value: int | None, info) -> int | None:
        start_minute = info.data.get("rescheduled_start_minute")
        if (start_minute is None) != (value is None):
            raise ValueError("Rescheduled start and end minutes must both be set")
        if start_minute is not None and value is not None and value <= start_minute:
            raise ValueError("Rescheduled end minute must be greater than start minute")
        return value

    @model_validator(mode="after")
    def validate_reschedule_fields(self) -> "SessionOccurrenceExceptionCreate":
        has_reschedule_fields = any(
            value is not None
            for value in (self.rescheduled_date, self.rescheduled_start_minute, self.rescheduled_end_minute)
        )
        if self.status == "rescheduled":
            if not all(
                value is not None
                for value in (self.rescheduled_date, self.rescheduled_start_minute, self.rescheduled_end_minute)
            ):
                raise ValueError("Rescheduled occurrences require date, start minute, and end minute")
        elif has_reschedule_fields:
            raise ValueError("Reschedule fields are only allowed when status is rescheduled")
        return self


class SessionOccurrenceExceptionRead(TimestampedRead, ORMModel):
    id: int
    session_id: int
    occurrence_date: date
    status: str
    rescheduled_date: date | None = None
    rescheduled_start_minute: int | None = None
    rescheduled_end_minute: int | None = None
    notes: str
    changed_by_user_id: int | None = None


class CentreClosureCreate(BaseModel):
    name: str
    closure_type: str
    start_date: date
    end_date: date
    notes: str = ""

    @field_validator("closure_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"holiday", "closure"}:
            raise ValueError("closure_type must be holiday or closure")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date is not None and value < start_date:
            raise ValueError("end_date cannot be before start_date")
        return value


class CentreClosureRead(TimestampedRead, CentreClosureCreate, ORMModel):
    id: int


class TeacherLeaveCreate(DatedWindowBase):
    teacher_id: int


class TeacherLeaveRead(TimestampedRead, TeacherLeaveCreate, ORMModel):
    id: int


class StudentAbsenceCreate(DatedWindowBase):
    student_id: int


class StudentAbsenceRead(TimestampedRead, StudentAbsenceCreate, ORMModel):
    id: int


class OccurrenceRead(BaseModel):
    session_id: int
    occurrence_date: date
    weekday: int
    effective_date: date
    start_minute: int
    end_minute: int
    teacher_id: int
    student_id: int
    subject: str
    base_status: str
    occurrence_status: str
    impact_reasons: list[str] = Field(default_factory=list)
    notes: str = ""


class OccurrenceQuery(BaseModel):
    date_from: date
    date_to: date
    teacher_id: int | None = None
    student_id: int | None = None

    @field_validator("date_to")
    @classmethod
    def validate_dates(cls, value: date, info) -> date:
        date_from = info.data.get("date_from")
        if date_from is not None and value < date_from:
            raise ValueError("date_to cannot be before date_from")
        return value
