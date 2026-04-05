from datetime import date

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    today: date
    teacher_count: int
    student_count: int
    recurring_session_count: int
    upcoming_occurrences: list[dict] = Field(default_factory=list)
    conflict_occurrences: list[dict] = Field(default_factory=list)
    unassigned_students: list[dict] = Field(default_factory=list)
    closures: list[dict] = Field(default_factory=list)
