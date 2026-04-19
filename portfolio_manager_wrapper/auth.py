"""
Authentication and token management for Portfolio Manager Wrapper.

Features:
- Automatic login
- Token caching
- Background refresh before expiry
- On-demand refresh on 401 errors
"""

import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

import httpx

from .exceptions import AuthenticationError, ConnectionError, APIError

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Token information with expiry tracking."""

    access_token: str
    token_type: str
    expires_in: int
    expires_at: float  # Unix timestamp

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired or will expire within buffer."""
        return time.time() >= (self.expires_at - buffer_seconds)

    def time_until_expiry(self) -> float:
        """Return seconds until token expires (negative if expired)."""
        return self.expires_at - time.time()


class TokenManager:
    """Manages authentication tokens with automatic refresh."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self._token: Optional[TokenInfo] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

    def login(self, username: str, password: str) -> TokenInfo:
        """Login and obtain new token."""
        self._username = username
        self._password = password

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/auth/login",
                    data={"username": username, "password": password},
                )

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid username or password",
                        {"username": username}
                    )

                response.raise_for_status()
                data = response.json()

                token = TokenInfo(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "bearer"),
                    expires_in=data.get("expires_in", 1800),  # Default 30 min
                    expires_at=time.time() + data.get("expires_in", 1800),
                )

                self._token = token
                logger.info(
                    f"Successfully logged in as {username}. "
                    f"Token expires in {token.expires_in} seconds."
                )
                return token

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to API server at {self.base_url}. "
                f"Is the server running?",
                {"original_error": str(e)}
            )
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"Login failed: {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.text else {}
            )
        except Exception as e:
            raise AuthenticationError(
                f"Login failed: {str(e)}",
                {"username": username}
            )

    def ensure_token(self, buffer_seconds: int = 60) -> str:
        """Get valid token, refreshing if necessary."""
        if self._token is None:
            if not self._username or not self._password:
                raise AuthenticationError(
                    "No token available and no credentials for auto-login. "
                    "Call login() first or provide credentials in Config."
                )
            logger.info("No token available, performing auto-login...")
            self.login(self._username, self._password)

        if self._token.is_expired(buffer_seconds):
            logger.info("Token expired or expiring soon, refreshing...")
            self.login(self._username, self._password)

        return self._token.access_token

    def get_auth_header(self) -> dict:
        """Get Authorization header with current token."""
        token = self.ensure_token()
        return {"Authorization": f"Bearer {token}"}

    def clear_token(self):
        """Clear cached token (force re-login)."""
        self._token = None
        logger.debug("Token cleared")

    @property
    def is_authenticated(self) -> bool:
        """Check if currently have a valid token."""
        return self._token is not None and not self._token.is_expired()

    @property
    def token_expires_at(self) -> Optional[float]:
        """Get token expiry timestamp."""
        return self._token.expires_at if self._token else None
