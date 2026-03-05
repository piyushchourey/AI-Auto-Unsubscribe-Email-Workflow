"""Authentication service: verify credentials and issue tokens."""
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional

from config import settings
from core.security import create_access_token, verify_password
from database import SessionLocal, User


class LoginRateLimiter:
    """In-memory rate limiter for login attempts per IP."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Return True if the key (e.g. IP) is under the limit."""
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - self.window
            self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
            if len(self._attempts[key]) >= self.max_attempts:
                return False
            self._attempts[key].append(now)
            return True


# Global rate limiter: 5 attempts per IP per minute (configurable via settings)
_login_limiter = LoginRateLimiter(
    max_attempts=getattr(settings, "login_rate_limit_per_minute", 5),
    window_seconds=60,
)


def check_login_rate_limit(ip_address: Optional[str]) -> bool:
    """Return True if login is allowed for this IP."""
    key = ip_address or "unknown"
    return _login_limiter.is_allowed(key)


def get_user_by_email(email: str) -> Optional[User]:
    """Fetch user by email (case-insensitive)."""
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email.strip().lower()).first()
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Verify credentials and return User if valid."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_token_for_user(user: User) -> str:
    """Create JWT access token for user."""
    return create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
