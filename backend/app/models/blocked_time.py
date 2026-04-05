from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StudentBlockedTime(Base):
    __tablename__ = "student_blocked_times"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="student_blocked_weekday_range"),
        CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="student_blocked_minute_range"),
        UniqueConstraint("student_id", "weekday", "start_minute", "end_minute", name="uq_student_blocked_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    student = relationship("Student", back_populates="blocked_times")
