"""
Portfolio Manager Wrapper

Python wrapper for Portfolio Manager API with sync and async support.
Provides convenient class-based interface with automatic authentication,
token refresh, and comprehensive error handling.

Usage:
    # Synchronous
    from portfolio_manager_wrapper import PortfolioManager_API

    with PortfolioManager_API() as api:
        transactions = api.get_transactions()

    # Asynchronous
    from portfolio_manager_wrapper import PortfolioManager_API_Async

    async with PortfolioManager_API_Async() as api:
        transactions = await api.get_transactions()
"""

__version__ = "0.1.0"
__app_name__ = "Portfolio Manager Wrapper"
__min_api_version__ = "0.2.0"
__max_api_version__ = "0.3.0"

from .sync import PortfolioManager_API
from .async_client import PortfolioManager_API_Async
from .exceptions import (
    PortfolioManagerError,
    AuthenticationError,
    ConnectionError,
    APIError,
    ConfigError,
    TokenExpiredError,
)

__all__ = [
    "PortfolioManager_API",
    "PortfolioManager_API_Async",
    "PortfolioManagerError",
    "AuthenticationError",
    "ConnectionError",
    "APIError",
    "ConfigError",
    "TokenExpiredError",
    "__version__",
]
