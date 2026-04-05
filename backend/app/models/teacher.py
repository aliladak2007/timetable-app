from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    subject_tags: Mapped[str] = mapped_column(Text, default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    availability_slots = relationship("AvailabilitySlot", back_populates="teacher", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="teacher")
    leave_blocks = relationship("TeacherLeave", back_populates="teacher", cascade="all, delete-orphan")
    linked_users = relationship("User", back_populates="linked_teacher")
