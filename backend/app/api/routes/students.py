from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import Student, StudentBlockedTime, StudentPreference, User
from app.schemas.student import (
    StudentBlockedTimeCreate,
    StudentCreate,
    StudentPreferenceCreate,
    StudentRead,
    StudentUpdate,
)
from app.services.access import AccessScope, apply_student_scope, get_student_or_404
from app.services.audit import write_audit_log


router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
def list_students(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[Student]:
    return list(
        db.scalars(
            apply_student_scope(select(Student), scope)
            .options(selectinload(Student.preferences), selectinload(Student.blocked_times))
            .order_by(Student.full_name)
        )
    )


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
) -> Student:
    student = Student(**payload.model_dump())
    db.add(student)
    db.flush()
    write_audit_log(
        db,
        action="student.created",
        entity_type="student",
        entity_id=str(student.id),
        summary=f"Student created: {payload.full_name}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> Student:
    return get_student_or_404(
        db,
        scope,
        student_id,
        stmt=(
            select(Student)
            .options(selectinload(Student.preferences), selectinload(Student.blocked_times))
        ),
    )


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> Student:
    student = get_student_or_404(
        db,
        scope,
        student_id,
        stmt=(
            select(Student)
            .options(selectinload(Student.preferences), selectinload(Student.blocked_times))
        ),
    )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    db.add(student)
    write_audit_log(
        db,
        action="student.updated",
        entity_type="student",
        entity_id=str(student.id),
        summary="Student profile updated",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    write_audit_log(
        db,
        action="student.deleted",
        entity_type="student",
        entity_id=str(student.id),
        summary=f"Student deleted: {student.full_name}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(student)
    db.commit()


@router.put("/{student_id}/preferences", response_model=StudentRead)
def replace_student_preferences(
    student_id: int,
    payload: list[StudentPreferenceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> Student:
    student = get_student_or_404(
        db,
        scope,
        student_id,
        stmt=(
            select(Student)
            .options(selectinload(Student.preferences), selectinload(Student.blocked_times))
        ),
    )

    student.preferences.clear()
    student.preferences.extend(StudentPreference(**item.model_dump()) for item in payload)
    db.add(student)
    write_audit_log(
        db,
        action="student.preferences.replaced",
        entity_type="student",
        entity_id=str(student.id),
        summary=f"Replaced {len(payload)} student preference windows",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(student)
    return student


@router.put("/{student_id}/blocked-times", response_model=StudentRead)
def replace_student_blocked_times(
    student_id: int,
    payload: list[StudentBlockedTimeCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> Student:
    student = get_student_or_404(
        db,
        scope,
        student_id,
        stmt=(
            select(Student)
            .options(selectinload(Student.preferences), selectinload(Student.blocked_times))
        ),
    )

    student.blocked_times.clear()
    student.blocked_times.extend(StudentBlockedTime(**item.model_dump()) for item in payload)
    db.add(student)
    write_audit_log(
        db,
        action="student.blocked_times.replaced",
        entity_type="student",
        entity_id=str(student.id),
        summary=f"Replaced {len(payload)} student blocked windows",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(student)
    return student
