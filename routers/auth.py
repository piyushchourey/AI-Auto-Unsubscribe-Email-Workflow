"""Auth router: login and current user."""
from fastapi import APIRouter, Depends, Request, HTTPException, status

from config import settings
from core.dependencies import get_current_user
from database import User
from models import LoginRequest, TokenResponse, UserResponse
from services.auth_service import (
    authenticate_user,
    check_login_rate_limit,
    create_token_for_user,
)
from services.activity_service import ActivityService
from deps import get_activity_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    activity: ActivityService = Depends(get_activity_service),
):
    """
    Authenticate with email and password. Returns a JWT access token.
    Rate limited per IP. Use Authorization: Bearer <token> on protected endpoints.
    """
    ip_address = request.client.host if request.client else None
    if not check_login_rate_limit(ip_address):
        activity.log(user_id=None, action="login_rate_limited", resource="auth", ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )
    user = authenticate_user(body.email.strip().lower(), body.password)
    if not user:
        activity.log(
            user_id=None,
            action="login_failed",
            resource="auth",
            details={"email": body.email.strip().lower()},
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_token_for_user(user)
    activity.log(
        user_id=user.id,
        action="login_success",
        resource="auth",
        details={"email": user.email},
        ip_address=ip_address,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user (id, email, role)."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )
