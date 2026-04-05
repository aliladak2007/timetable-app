from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SessionOccurrenceException(TimestampMixin, Base):
    __tablename__ = "session_occurrence_exceptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('cancelled', 'completed', 'rescheduled', 'missed', 'holiday_affected')",
            name="occurrence_exception_status_check",
        ),
        UniqueConstraint("session_id", "occurrence_date", name="uq_session_occurrence_exception"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    occurrence_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    rescheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    rescheduled_start_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rescheduled_end_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    session = relationship("Session", back_populates="occurrence_exceptions")


class CentreClosure(TimestampMixin, Base):
    __tablename__ = "centre_closures"
    __table_args__ = (
        CheckConstraint("closure_type IN ('holiday', 'closure')", name="centre_closure_type_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    closure_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class TeacherLeave(TimestampMixin, Base):
    __tablename__ = "teacher_leave_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    teacher = relationship("Teacher", back_populates="leave_blocks")


class StudentAbsence(TimestampMixin, Base):
    __tablename__ = "student_absence_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    student = relationship("Student", back_populates="absences")
