from pydantic import BaseModel, field_validator, model_validator


class CalendarFeedTokenCreate(BaseModel):
    owner_type: str
    owner_id: int | None = None
    label: str = ""

    @field_validator("owner_type")
    @classmethod
    def validate_owner_type(cls, value: str) -> str:
        if value not in {"teacher", "student", "centre"}:
            raise ValueError("owner_type must be teacher, student, or centre")
        return value

    @model_validator(mode="after")
    def validate_owner_id(self) -> "CalendarFeedTokenCreate":
        if self.owner_type == "centre":
            if self.owner_id is not None:
                raise ValueError("Centre feeds must not include an owner_id")
        elif self.owner_id is None:
            raise ValueError("Teacher and student feeds require an owner_id")
        return self


class CalendarFeedTokenRead(BaseModel):
    id: int
    owner_type: str
    owner_id: int | None = None
    label: str
    active: bool
    token: str | None = None
