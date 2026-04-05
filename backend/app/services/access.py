from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    CalendarFeedToken,
    Session as SessionModel,
    Student,
    StudentAbsence,
    Teacher,
    TeacherLeave,
    User,
)


@dataclass(frozen=True)
class AccessScope:
    user: User
    linked_teacher_id: int | None = None

    @property
    def is_admin(self) -> bool:
        return self.user.role == "admin"

    @property
    def requires_teacher_scope(self) -> bool:
        return not self.is_admin


def build_access_scope(db: Session, user: User) -> AccessScope:
    if user.role == "admin":
        return AccessScope(user=user)

    if user.linked_teacher_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not linked to a teacher.",
        )

    teacher_exists = db.scalar(select(Teacher.id).where(Teacher.id == user.linked_teacher_id))
    if teacher_exists is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is linked to a teacher that no longer exists.",
        )

    return AccessScope(user=user, linked_teacher_id=user.linked_teacher_id)


def apply_teacher_scope(stmt: Select, scope: AccessScope) -> Select:
    if scope.is_admin:
        return stmt
    return stmt.where(Teacher.id == scope.linked_teacher_id)


def apply_session_scope(stmt: Select, scope: AccessScope) -> Select:
    if scope.is_admin:
        return stmt
    return stmt.where(SessionModel.teacher_id == scope.linked_teacher_id)


def apply_student_scope(stmt: Select, scope: AccessScope) -> Select:
    if scope.is_admin:
        return stmt
    return (
        stmt.join(SessionModel, SessionModel.student_id == Student.id)
        .where(SessionModel.teacher_id == scope.linked_teacher_id)
        .distinct()
    )


def apply_teacher_leave_scope(stmt: Select, scope: AccessScope) -> Select:
    if scope.is_admin:
        return stmt
    return stmt.where(TeacherLeave.teacher_id == scope.linked_teacher_id)


def apply_student_absence_scope(stmt: Select, scope: AccessScope) -> Select:
    if scope.is_admin:
        return stmt
    return (
        stmt.join(SessionModel, SessionModel.student_id == StudentAbsence.student_id)
        .where(SessionModel.teacher_id == scope.linked_teacher_id)
        .distinct()
    )


def get_teacher_or_404(db: Session, scope: AccessScope, teacher_id: int, *, stmt: Select | None = None) -> Teacher:
    query = stmt if stmt is not None else select(Teacher)
    teacher = db.scalar(apply_teacher_scope(query.where(Teacher.id == teacher_id), scope))
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


def get_session_or_404(db: Session, scope: AccessScope, session_id: int, *, stmt: Select | None = None) -> SessionModel:
    query = stmt if stmt is not None else select(SessionModel)
    session = db.scalar(apply_session_scope(query.where(SessionModel.id == session_id), scope))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def get_student_or_404(db: Session, scope: AccessScope, student_id: int, *, stmt: Select | None = None) -> Student:
    query = stmt if stmt is not None else select(Student)
    student = db.scalar(apply_student_scope(query.where(Student.id == student_id), scope))
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


def get_teacher_leave_or_404(db: Session, scope: AccessScope, leave_id: int) -> TeacherLeave:
    leave = db.scalar(apply_teacher_leave_scope(select(TeacherLeave).where(TeacherLeave.id == leave_id), scope))
    if leave is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher leave not found")
    return leave


def get_student_absence_or_404(db: Session, scope: AccessScope, absence_id: int) -> StudentAbsence:
    absence = db.scalar(apply_student_absence_scope(select(StudentAbsence).where(StudentAbsence.id == absence_id), scope))
    if absence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student absence not found")
    return absence


def ensure_teacher_access(scope: AccessScope, teacher_id: int) -> None:
    if not scope.is_admin and teacher_id != scope.linked_teacher_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")


def ensure_student_access(db: Session, scope: AccessScope, student_id: int) -> None:
    if scope.is_admin:
        return
    student_exists = db.scalar(
        select(Student.id)
        .join(SessionModel, SessionModel.student_id == Student.id)
        .where(Student.id == student_id, SessionModel.teacher_id == scope.linked_teacher_id)
        .limit(1)
    )
    if student_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")


def enforce_occurrence_filters(
    db: Session,
    scope: AccessScope,
    *,
    teacher_id: int | None,
    student_id: int | None,
) -> tuple[int | None, int | None]:
    resolved_teacher_id = teacher_id
    if scope.requires_teacher_scope:
        if teacher_id is not None and teacher_id != scope.linked_teacher_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
        resolved_teacher_id = scope.linked_teacher_id

    if student_id is not None and scope.requires_teacher_scope:
        ensure_student_access(db, scope, student_id)

    return resolved_teacher_id, student_id


def ensure_calendar_owner_access(
    db: Session,
    scope: AccessScope,
    *,
    owner_type: str,
    owner_id: int | None,
) -> None:
    if owner_type == "centre":
        if not scope.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Centre-wide calendar export is admin only")
        return

    if owner_type == "teacher":
        if owner_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher calendar export requires an owner_id")
        ensure_teacher_access(scope, owner_id)
        return

    if owner_type == "student":
        if owner_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student calendar export requires an owner_id")
        ensure_student_access(db, scope, owner_id)
        return

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="owner_type must be teacher, student, or centre")


def get_calendar_feed_or_404(db: Session, feed_id: int) -> CalendarFeedToken:
    feed = db.get(CalendarFeedToken, feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar feed not found")
    return feed
