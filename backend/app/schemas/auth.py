from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.schemas.common import ORMModel, TimestampedRead


def validate_strong_password(value: str) -> str:
    if len(value) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if value.lower() == value or value.upper() == value:
        raise ValueError("Password must include mixed case letters")
    if not any(char.isdigit() for char in value):
        raise ValueError("Password must include at least one number")
    if not any(not char.isalnum() for char in value):
        raise ValueError("Password must include at least one symbol")
    return value


class BootstrapStatus(BaseModel):
    needs_bootstrap: bool


class BootstrapAdminRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str
    linked_teacher_id: int | None = None
    active: bool = True

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"admin", "staff_scheduler", "viewer"}:
            raise ValueError("role must be admin, staff_scheduler, or viewer")
        return value

    @model_validator(mode="after")
    def validate_teacher_link(self) -> "UserCreate":
        if self.role == "admin" and self.linked_teacher_id is not None:
            raise ValueError("admin users cannot be linked to a teacher")
        if self.role != "admin" and self.linked_teacher_id is None:
            raise ValueError("non-admin users must be linked to a teacher")
        return self


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    linked_teacher_id: int | None = None
    active: bool | None = None
    must_change_password: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is not None and value not in {"admin", "staff_scheduler", "viewer"}:
            raise ValueError("role must be admin, staff_scheduler, or viewer")
        return value


class UserRead(TimestampedRead, ORMModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    linked_teacher_id: int | None = None
    active: bool
    must_change_password: bool
    last_login_at: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserRead
