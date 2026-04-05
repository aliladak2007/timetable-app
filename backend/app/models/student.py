from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parent_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    preferences = relationship("StudentPreference", back_populates="student", cascade="all, delete-orphan")
    blocked_times = relationship("StudentBlockedTime", back_populates="student", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="student")
    absences = relationship("StudentAbsence", back_populates="student", cascade="all, delete-orphan")
