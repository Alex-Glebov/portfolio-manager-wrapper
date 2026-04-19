"""
Custom exceptions for Portfolio Manager Wrapper.

All business logic errors are wrapped in PortfolioManagerError hierarchy.
Programming errors (ValueError, TypeError, etc.) are not wrapped.
"""


class PortfolioManagerError(Exception):
    """Base exception for all Portfolio Manager business logic errors.

    This exception and its subclasses represent errors that users should
    handle in their code (authentication failures, API errors, config issues).

    Programming errors (ValueError, TypeError, etc.) are NOT wrapped
    and should be fixed in the calling code.
    """

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AuthenticationError(PortfolioManagerError):
    """Raised when authentication fails.

    Possible causes:
    - Invalid username/password
    - Token expired and refresh failed
    - User not authorized for portfolio
    """
    pass


class ConnectionError(PortfolioManagerError):
    """Raised when cannot connect to API server.

    Possible causes:
    - Server not running
    - Wrong host/port
    - Network issues
    - Timeout
    """
    pass


class APIError(PortfolioManagerError):
    """Raised when API returns error response.

    Attributes:
        status_code: HTTP status code from API
        response: Full response object or dict
    """

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class ConfigError(PortfolioManagerError):
    """Raised when configuration is invalid or missing.

    Possible causes:
    - Required config value missing
    - Invalid config file format
    - Missing password (no env var, no config, no parameter)
    """

    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message)
        self.suggestion = suggestion

    def __str__(self) -> str:
        msg = self.message
        if self.suggestion:
            msg += f"\nSuggestion: {self.suggestion}"
        return msg


class TokenExpiredError(AuthenticationError):
    """Raised when token expires and automatic refresh fails.

    This is a subclass of AuthenticationError - usually caught
    and handled internally with automatic retry.
    """
    pass


class ValidationError(PortfolioManagerError):
    """Raised when request data is invalid.

    Possible causes:
    - Missing required fields
    - Invalid data types
    - Business rule violations
    """
    pass
