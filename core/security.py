"""Password hashing and JWT token handling."""
from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from config import settings

# bcrypt has a 72-byte limit; truncate to avoid "password cannot be longer than 72 bytes"
BCRYPT_MAX_BYTES = 72
BCRYPT_ROUNDS = 12


def _truncate_for_bcrypt(password: str) -> bytes:
    """Truncate password to 72 bytes (UTF-8) for bcrypt. Strips whitespace. Returns bytes."""
    s = (password or "").strip()
    b = s.encode("utf-8")
    if len(b) <= BCRYPT_MAX_BYTES:
        return b
    return b[:BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    """Hash a plain-text password (truncated to 72 bytes for bcrypt)."""
    p = _truncate_for_bcrypt(plain)
    return bcrypt.hashpw(p, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hash."""
    p = _truncate_for_bcrypt(plain)
    try:
        return bcrypt.checkpw(p, hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT; returns payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None
