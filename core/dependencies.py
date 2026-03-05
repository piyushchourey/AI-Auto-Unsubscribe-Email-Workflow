"""FastAPI dependencies for auth and role-based access."""
from typing import Annotated, Optional

from fastapi import Depends, Request

from core.exceptions import AuthError, ForbiddenError
from core.security import decode_token
from database import SessionLocal
from database import User as UserModel


def get_db_session():
    """Yield a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_token_from_header(request: Request) -> Optional[str]:
    """
    Get Bearer token from Authorization header.
    Uses raw header so missing/malformed header gives 401 from get_current_user, not 422.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.strip().upper().startswith("BEARER "):
        return None
    parts = auth.strip().split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return None
    return parts[1].strip()


def get_current_user(
    token: Annotated[Optional[str], Depends(_get_token_from_header)],
) -> UserModel:
    """Validate JWT and return the current user. Raises AuthError if invalid."""
    if not token:
        raise AuthError("Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise AuthError("Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Invalid token payload")
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise AuthError("Invalid token payload")
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.id == uid).first()
        if not user:
            raise AuthError("User not found")
        if not user.is_active:
            raise AuthError("User account is disabled")
        return user
    finally:
        db.close()


def _require_admin(current_user: Annotated[UserModel, Depends(get_current_user)]) -> UserModel:
    if current_user.role != "admin":
        raise ForbiddenError("Requires role: admin")
    return current_user


def _require_operator(current_user: Annotated[UserModel, Depends(get_current_user)]) -> UserModel:
    if current_user.role not in ("admin", "operator"):
        raise ForbiddenError("Requires role: admin or operator")
    return current_user


def _require_viewer(current_user: Annotated[UserModel, Depends(get_current_user)]) -> UserModel:
    if current_user.role not in ("admin", "operator", "viewer"):
        raise ForbiddenError("Requires role: admin, operator, or viewer")
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[UserModel, Depends(get_current_user)]
RequireAdmin = Annotated[UserModel, Depends(_require_admin)]
RequireOperator = Annotated[UserModel, Depends(_require_operator)]
RequireViewer = Annotated[UserModel, Depends(_require_viewer)]
