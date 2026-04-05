from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StudentPreference(Base):
    __tablename__ = "student_preferences"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="student_preference_weekday_range"),
        CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="student_preference_minute_range"),
        CheckConstraint("priority >= 1 AND priority <= 5", name="student_preference_priority_range"),
        UniqueConstraint("student_id", "weekday", "start_minute", "end_minute", name="uq_student_preference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    student = relationship("Student", back_populates="preferences")
