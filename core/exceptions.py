"""Custom exceptions for consistent error handling."""


class AuthError(Exception):
    """Authentication failed (invalid/missing token or credentials)."""
    def __init__(self, detail: str = "Could not validate credentials"):
        self.detail = detail
        super().__init__(detail)


class ForbiddenError(Exception):
    """User is authenticated but not allowed to perform this action."""
    def __init__(self, detail: str = "Not enough permissions"):
        self.detail = detail
        super().__init__(detail)
