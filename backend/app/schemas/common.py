from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedRead(ORMModel):
    created_at: datetime
    updated_at: datetime


class TimeWindowBase(BaseModel):
    weekday: int
    start_minute: int
    end_minute: int

    @field_validator("weekday")
    @classmethod
    def validate_weekday(cls, value: int) -> int:
        if value < 0 or value > 6:
            raise ValueError("weekday must be between 0 and 6")
        return value

    @field_validator("start_minute", "end_minute")
    @classmethod
    def validate_minutes(cls, value: int) -> int:
        if value < 0 or value > 24 * 60:
            raise ValueError("minute values must be between 0 and 1440")
        if value % 15 != 0:
            raise ValueError("minute values must be in 15-minute increments")
        return value

    @field_validator("end_minute")
    @classmethod
    def validate_order(cls, value: int, info) -> int:
        start_minute = info.data.get("start_minute")
        if start_minute is not None and value <= start_minute:
            raise ValueError("end_minute must be greater than start_minute")
        return value


class DatedWindowBase(BaseModel):
    start_date: date
    end_date: date
    start_minute: int | None = None
    end_minute: int | None = None
    reason: str = ""
    notes: str = ""

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date is not None and value < start_date:
            raise ValueError("end_date cannot be before start_date")
        return value

    @field_validator("start_minute", "end_minute")
    @classmethod
    def validate_optional_minutes(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 0 or value > 24 * 60:
            raise ValueError("minute values must be between 0 and 1440")
        if value % 15 != 0:
            raise ValueError("minute values must be in 15-minute increments")
        return value

    @field_validator("end_minute")
    @classmethod
    def validate_optional_order(cls, value: int | None, info) -> int | None:
        start_minute = info.data.get("start_minute")
        if (start_minute is None) != (value is None):
            raise ValueError("start_minute and end_minute must both be set or both be omitted")
        if value is not None and start_minute is not None and value <= start_minute:
            raise ValueError("end_minute must be greater than start_minute")
        return value


Email = EmailStr
