from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CentreClosure, Session as SessionModel, Student, Teacher
from app.schemas.dashboard import DashboardSummary
from app.services.access import AccessScope
from app.services.scheduling import build_occurrences


def build_dashboard(db: Session, scope: AccessScope) -> DashboardSummary:
    today = date.today()
    occurrences = build_occurrences(
        db,
        date_from=today,
        date_to=today + timedelta(days=7),
        teacher_id=None if scope.is_admin else scope.linked_teacher_id,
    )
    upcoming = [
        occurrence.model_dump()
        for occurrence in occurrences
        if occurrence.occurrence_status in {"scheduled", "rescheduled"} and occurrence.effective_date >= today
    ][:12]
    conflicts = [occurrence.model_dump() for occurrence in occurrences if occurrence.impact_reasons][:12]
    if scope.is_admin:
        unassigned_students = [
            {"id": student.id, "full_name": student.full_name}
            for student in db.scalars(
                select(Student)
                .outerjoin(SessionModel, SessionModel.student_id == Student.id)
                .where(Student.active.is_(True))
                .group_by(Student.id)
                .having(func.count(SessionModel.id) == 0)
                .order_by(Student.full_name)
            )
        ]
        closures = [
            {"id": closure.id, "name": closure.name, "start_date": closure.start_date, "end_date": closure.end_date}
            for closure in db.scalars(
                select(CentreClosure)
                .where(CentreClosure.end_date >= today)
                .order_by(CentreClosure.start_date)
                .limit(10)
            )
        ]
        teacher_count = db.scalar(select(func.count()).select_from(Teacher)) or 0
        student_count = db.scalar(select(func.count()).select_from(Student)) or 0
        recurring_session_count = db.scalar(select(func.count()).select_from(SessionModel)) or 0
    else:
        unassigned_students = []
        closures = []
        teacher_count = 1
        student_count = db.scalar(
            select(func.count(func.distinct(Student.id)))
            .select_from(Student)
            .join(SessionModel, SessionModel.student_id == Student.id)
            .where(SessionModel.teacher_id == scope.linked_teacher_id)
        ) or 0
        recurring_session_count = db.scalar(
            select(func.count())
            .select_from(SessionModel)
            .where(SessionModel.teacher_id == scope.linked_teacher_id)
        ) or 0
    return DashboardSummary(
        today=today,
        teacher_count=teacher_count,
        student_count=student_count,
        recurring_session_count=recurring_session_count,
        upcoming_occurrences=upcoming,
        conflict_occurrences=conflicts,
        unassigned_students=unassigned_students,
        closures=closures,
    )
