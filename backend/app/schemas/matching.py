from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.schemas.student import StudentBlockedTimeCreate, StudentPreferenceCreate


class MatchSuggestionRequest(BaseModel):
    teacher_id: int
    duration_minutes: int
    student_id: int | None = None
    student_preferences: list[StudentPreferenceCreate] = Field(default_factory=list)
    student_blocked_times: list[StudentBlockedTimeCreate] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    increment_minutes: int = 15
    include_rejections: bool = True
    max_rejections: int = 10

    @field_validator("duration_minutes", "increment_minutes")
    @classmethod
    def validate_positive_minutes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("minute values must be positive")
        return value


class MatchSuggestion(BaseModel):
    weekday: int
    start_minute: int
    end_minute: int
    score: int
    reasons: list[str]
    score_breakdown: dict[str, int]


class RejectedSlot(BaseModel):
    weekday: int
    start_minute: int
    end_minute: int
    reasons: list[str]


class MatchSuggestionResponse(BaseModel):
    suggestions: list[MatchSuggestion]
    rejected_slots: list[RejectedSlot] = Field(default_factory=list)
