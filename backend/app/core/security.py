from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings


settings = get_settings()
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(*, user_id: int, email: str, role: str, session_version: int) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "sv": session_version,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.resolved_jwt_secret, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.resolved_jwt_secret, algorithms=["HS256"])
