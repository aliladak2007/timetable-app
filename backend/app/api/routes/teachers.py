from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_access_scope, require_roles
from app.core.db import get_db
from app.models import AvailabilitySlot, Teacher, User
from app.schemas.teacher import AvailabilitySlotCreate, TeacherCreate, TeacherRead, TeacherUpdate
from app.services.access import AccessScope, apply_teacher_scope, get_teacher_or_404
from app.services.audit import write_audit_log


router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherRead])
def list_teachers(
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> list[Teacher]:
    return list(
        db.scalars(
            apply_teacher_scope(select(Teacher), scope)
            .options(selectinload(Teacher.availability_slots))
            .order_by(Teacher.full_name)
        )
    )


@router.post("", response_model=TeacherRead, status_code=status.HTTP_201_CREATED)
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> Teacher:
    teacher = Teacher(**payload.model_dump())
    db.add(teacher)
    db.flush()
    write_audit_log(
        db,
        action="teacher.created",
        entity_type="teacher",
        entity_id=str(teacher.id),
        summary=f"Teacher created: {payload.full_name}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    scope: AccessScope = Depends(get_access_scope),
) -> Teacher:
    return get_teacher_or_404(db, scope, teacher_id, stmt=select(Teacher).options(selectinload(Teacher.availability_slots)))


@router.patch("/{teacher_id}", response_model=TeacherRead)
def update_teacher(
    teacher_id: int,
    payload: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> Teacher:
    teacher = get_teacher_or_404(db, scope, teacher_id, stmt=select(Teacher).options(selectinload(Teacher.availability_slots)))

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(teacher, key, value)
    db.add(teacher)
    write_audit_log(
        db,
        action="teacher.updated",
        entity_type="teacher",
        entity_id=str(teacher.id),
        summary="Teacher profile updated",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    write_audit_log(
        db,
        action="teacher.deleted",
        entity_type="teacher",
        entity_id=str(teacher.id),
        summary=f"Teacher deleted: {teacher.full_name}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(teacher)
    db.commit()


@router.put("/{teacher_id}/availability", response_model=TeacherRead)
def replace_teacher_availability(
    teacher_id: int,
    payload: list[AvailabilitySlotCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff_scheduler")),
    scope: AccessScope = Depends(get_access_scope),
) -> Teacher:
    teacher = get_teacher_or_404(db, scope, teacher_id, stmt=select(Teacher).options(selectinload(Teacher.availability_slots)))

    teacher.availability_slots.clear()
    teacher.availability_slots.extend(AvailabilitySlot(**item.model_dump()) for item in payload)
    db.add(teacher)
    write_audit_log(
        db,
        action="teacher.availability.replaced",
        entity_type="teacher",
        entity_id=str(teacher.id),
        summary=f"Replaced {len(payload)} teacher availability windows",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(teacher)
    return teacher
