from pydantic import Field

from app.schemas.common import Email, ORMModel, TimeWindowBase, TimestampedRead


class StudentPreferenceCreate(TimeWindowBase):
    priority: int = 1


class StudentBlockedTimeCreate(TimeWindowBase):
    reason: str = ""


class StudentPreferenceRead(ORMModel, StudentPreferenceCreate):
    id: int
    student_id: int


class StudentBlockedTimeRead(ORMModel, StudentBlockedTimeCreate):
    id: int
    student_id: int


class StudentCreate(ORMModel):
    full_name: str
    parent_name: str = ""
    contact_email: Email
    active: bool = True
    notes: str = ""


class StudentUpdate(ORMModel):
    full_name: str | None = None
    parent_name: str | None = None
    contact_email: Email | None = None
    active: bool | None = None
    notes: str | None = None


class StudentRead(TimestampedRead, StudentCreate):
    id: int
    preferences: list[StudentPreferenceRead] = Field(default_factory=list)
    blocked_times: list[StudentBlockedTimeRead] = Field(default_factory=list)
