"""Custom exceptions for the Huntrecht SDK."""


class HuntrechtError(Exception):
    """Base exception for all Huntrecht SDK errors."""

    def __init__(
        self, message: str, status_code: int | None = None, response: dict | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(HuntrechtError):
    """Raised when authentication fails."""

    pass


class RateLimitError(HuntrechtError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NotFoundError(HuntrechtError):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(HuntrechtError):
    """Raised when request validation fails."""

    pass


class PermissionError(HuntrechtError):  # noqa: A001
    """Raised when the user lacks permission for the operation."""

    pass
