from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models import User
from app.services.access import AccessScope, build_access_scope


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.active or user.session_version != payload.get("sv"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is no longer valid")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this action")
        return user

    return dependency


def get_access_scope(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccessScope:
    return build_access_scope(db, current_user)


def get_request_actor(request: Request, user: User | None = Depends(get_current_user)) -> dict:
    client_host = request.client.host if request.client else ""
    return {
        "user_id": user.id if user else None,
        "email": user.email if user else "",
        "client_host": client_host,
    }
