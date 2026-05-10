"""JWT helpers for admin panel auth.

Uses `bcrypt` directly (passlib is unmaintained and incompatible with
bcrypt >= 4.x — it accesses `bcrypt.__about__.__version__` which was
removed). bcrypt's 72-byte hard limit is handled here by truncation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 12

# bcrypt only inspects the first 72 bytes — truncate explicitly to avoid
# 4.x raising ValueError instead of silent truncation.
_BCRYPT_MAX_BYTES = 72


def _to_bytes_capped(plain: str) -> bytes:
    raw = plain.encode("utf-8")
    return raw[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bytes_capped(plain), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes_capped(plain), hashed.encode("ascii"))
    except Exception:
        return False


def create_access_token(subject: str, role: str = "admin") -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
