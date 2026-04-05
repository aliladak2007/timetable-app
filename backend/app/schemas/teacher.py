from pydantic import Field

from app.schemas.common import Email, ORMModel, TimeWindowBase, TimestampedRead


class AvailabilitySlotCreate(TimeWindowBase):
    pass


class AvailabilitySlotRead(ORMModel, TimeWindowBase):
    id: int
    teacher_id: int


class TeacherCreate(ORMModel):
    full_name: str
    email: Email
    subject_tags: str = ""
    active: bool = True
    notes: str = ""


class TeacherUpdate(ORMModel):
    full_name: str | None = None
    email: Email | None = None
    subject_tags: str | None = None
    active: bool | None = None
    notes: str | None = None


class TeacherRead(TimestampedRead, TeacherCreate):
    id: int
    availability_slots: list[AvailabilitySlotRead] = Field(default_factory=list)
