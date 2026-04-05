from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_access_scope, get_current_user, require_roles
from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Teacher, User
from app.schemas.auth import (
    AuthTokenResponse,
    BootstrapAdminRequest,
    BootstrapStatus,
    LoginRequest,
    PasswordChangeRequest,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.audit import write_audit_log
from app.services.access import build_access_scope
from app.services.rate_limit import rate_limiter


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _validate_linked_teacher(db: Session, linked_teacher_id: int | None) -> None:
    if linked_teacher_id is None:
        return
    if db.get(Teacher, linked_teacher_id) is None:
        raise HTTPException(status_code=404, detail="Linked teacher not found")


@router.get("/bootstrap-status", response_model=BootstrapStatus)
def bootstrap_status(db: Session = Depends(get_db)) -> BootstrapStatus:
    has_users = db.scalar(select(User.id).limit(1)) is not None
    return BootstrapStatus(needs_bootstrap=not has_users)


@router.post("/bootstrap-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: BootstrapAdminRequest, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User.id).limit(1)) is not None:
        raise HTTPException(status_code=409, detail="Bootstrap has already been completed")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin",
        active=True,
    )
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        action="auth.bootstrap_admin",
        entity_type="user",
        entity_id=str(user.id),
        summary="Initial admin account created",
        actor_email=payload.email,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> AuthTokenResponse:
    client_host = request.client.host if request.client else "unknown"
    rate_limiter.enforce(
        key=f"login:{client_host}:{payload.email.lower()}",
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )

    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        write_audit_log(
            db,
            action="auth.login_failed",
            entity_type="user",
            entity_id=payload.email,
            summary="Failed login attempt",
            actor_email=payload.email,
            outcome="denied",
            details={"client_host": client_host},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    try:
        build_access_scope(db, user)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            write_audit_log(
                db,
                action="auth.login_denied",
                entity_type="user",
                entity_id=str(user.id),
                summary=exc.detail,
                actor_user_id=user.id,
                actor_email=user.email,
                outcome="denied",
                details={"client_host": client_host},
            )
            db.commit()
        raise

    user.last_login_at = datetime.now(timezone.utc).isoformat()
    token, expires_at = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        session_version=user.session_version,
    )
    write_audit_log(
        db,
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        summary="User logged in",
        actor_user_id=user.id,
        actor_email=user.email,
        details={"client_host": client_host},
    )
    db.commit()
    return AuthTokenResponse(access_token=token, expires_at=expires_at, user=user)


@router.get("/me", response_model=UserRead)
def me(scope=Depends(get_access_scope)) -> User:
    return scope.user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    current_user.session_version += 1
    current_user.must_change_password = False
    db.add(current_user)
    write_audit_log(
        db,
        action="auth.password_changed",
        entity_type="user",
        entity_id=str(current_user.id),
        summary="Password changed",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name)))


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    _validate_linked_teacher(db, payload.linked_teacher_id)
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        linked_teacher_id=payload.linked_teacher_id,
        active=payload.active,
    )
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        action="auth.user_created",
        entity_type="user",
        entity_id=str(user.id),
        summary=f"User created with role {payload.role}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> User:
    user = _get_user_or_404(db, user_id)
    changes = payload.model_dump(exclude_unset=True)
    next_role = changes.get("role", user.role)
    next_linked_teacher_id = changes.get("linked_teacher_id", user.linked_teacher_id)
    if next_role == "admin":
        changes["linked_teacher_id"] = None
        next_linked_teacher_id = None
    elif next_linked_teacher_id is None:
        raise HTTPException(status_code=400, detail="Non-admin users must be linked to a teacher")

    _validate_linked_teacher(db, next_linked_teacher_id)

    if ("role" in changes and changes["role"] != user.role) or (
        "linked_teacher_id" in changes and changes["linked_teacher_id"] != user.linked_teacher_id
    ):
        user.session_version += 1
    for key, value in changes.items():
        setattr(user, key, value)
    db.add(user)
    write_audit_log(
        db,
        action="auth.user_updated",
        entity_type="user",
        entity_id=str(user.id),
        summary="User role or status updated",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        details=changes,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/force-logout", status_code=status.HTTP_204_NO_CONTENT)
def force_logout_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    user = _get_user_or_404(db, user_id)
    user.session_version += 1
    db.add(user)
    write_audit_log(
        db,
        action="auth.force_logout",
        entity_type="user",
        entity_id=str(user.id),
        summary="User sessions invalidated",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.commit()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> None:
    user = _get_user_or_404(db, user_id)
    write_audit_log(
        db,
        action="auth.user_deleted",
        entity_type="user",
        entity_id=str(user.id),
        summary=f"User deleted: {user.email}",
        actor_user_id=current_user.id,
        actor_email=current_user.email,
    )
    db.delete(user)
    db.commit()
