from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="session_weekday_range"),
        CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="session_minute_range"),
        CheckConstraint("duration_minutes = end_minute - start_minute", name="session_duration_matches_range"),
        CheckConstraint("status IN ('active', 'inactive')", name="session_status_check"),
        UniqueConstraint(
            "teacher_id",
            "student_id",
            "weekday",
            "start_minute",
            "end_minute",
            "start_date",
            name="uq_session_template",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    teacher = relationship("Teacher", back_populates="sessions")
    student = relationship("Student", back_populates="sessions")
    occurrence_exceptions = relationship("SessionOccurrenceException", back_populates="session", cascade="all, delete-orphan")
