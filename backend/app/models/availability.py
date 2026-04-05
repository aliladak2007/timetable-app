from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="availability_weekday_range"),
        CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name="availability_minute_range"),
        UniqueConstraint("teacher_id", "weekday", "start_minute", "end_minute", name="uq_availability_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    end_minute: Mapped[int] = mapped_column(Integer, nullable=False)

    teacher = relationship("Teacher", back_populates="availability_slots")
