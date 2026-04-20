"""
Configuration management for Portfolio Manager Wrapper.

Configuration priority (highest to lowest):
1. Function arguments (passed to init)
2. Environment variables
3. Config file (PortfolioManager_API_Config.ini)
4. Default values
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from configparser import ConfigParser

from .exceptions import ConfigError

logger = logging.getLogger(__name__)

# Environment variable names
ENV_HOST = "PORTFOLIO_MANAGER_HOST"
ENV_PORT = "PORTFOLIO_MANAGER_PORT"
ENV_USER = "PORTFOLIO_MANAGER_USER"
ENV_PASSWORD = "PORTFOLIO_MANAGER_PASSWORD"

DEFAULT_CONFIG_FILENAME = "PortfolioManager_API_Config.ini"


class Config:
    """Configuration manager with priority-based loading.

    Priority: args > env vars > config file > defaults
    """

    # Default values (lowest priority)
    DEFAULTS = {
        "host": "localhost",
        "port": 8000,
        "username": "admin",
        "password": "",  # Must be provided via env or parameter
        "timeout": 30,
        "verify_ssl": True,
        "token_refresh_buffer": 60,  # Refresh token 60 seconds before expiry
        "log_level": "INFO",
        "log_file": "portfolio_manager_wrapper.log",
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        token_refresh_buffer: Optional[int] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        """Initialize configuration with priority loading.

        Args:
            config_path: Path to config file (default: PortfolioManager_API_Config.ini)
            host: API server host
            port: API server port
            username: Login username
            password: Login password (should use env var instead)
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            token_refresh_buffer: Seconds before expiry to refresh token
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Path to log file
        """
        self._config_file_values = {}
        self._warnings = []

        # Load from config file
        config_file_path = config_path or DEFAULT_CONFIG_FILENAME
        self._load_config_file(config_file_path)

        # Build final config with priority
        self.host = self._get_value("host", host, ENV_HOST)
        self.port = self._get_value("port", port, ENV_PORT, int)
        self.username = self._get_value("username", username, ENV_USER)
        self.password = self._get_value("password", password, ENV_PASSWORD)
        self.timeout = self._get_value("timeout", timeout, None, int)
        self.verify_ssl = self._get_value("verify_ssl", verify_ssl, None, bool)
        self.token_refresh_buffer = self._get_value(
            "token_refresh_buffer", token_refresh_buffer, None, int
        )
        self.log_level = self._get_value("log_level", log_level, None)
        self.log_file = self._get_value("log_file", log_file, None)

        # Validate
        self._validate()

    def _load_config_file(self, config_path: str):
        """Load values from config file if it exists."""
        path = Path(config_path)
        if not path.exists():
            logger.debug(f"Config file not found: {config_path}")
            return

        try:
            parser = ConfigParser()
            parser.read(path)

            if "connection" in parser:
                conn = parser["connection"]
                self._config_file_values["host"] = conn.get("host")
                self._config_file_values["port"] = conn.getint("port", fallback=None)
                self._config_file_values["timeout"] = conn.getint("timeout", fallback=None)
                self._config_file_values["verify_ssl"] = conn.getboolean("verify_ssl", fallback=None)

            if "auth" in parser:
                auth = parser["auth"]
                self._config_file_values["username"] = auth.get("username")
                password = auth.get("password")
                if password:
                    self._config_file_values["password"] = password
                    self._warnings.append(
                        "WARNING: Password found in config file. "
                        f"Use environment variable {ENV_PASSWORD} instead for security."
                    )

            if "logging" in parser:
                log = parser["logging"]
                self._config_file_values["log_level"] = log.get("level")
                self._config_file_values["log_file"] = log.get("file")

            if "token" in parser:
                token = parser["token"]
                self._config_file_values["token_refresh_buffer"] = token.getint(
                    "refresh_buffer", fallback=None
                )

            logger.info(f"Loaded config from: {config_path}")

        except Exception as e:
            logger.warning(f"Error loading config file {config_path}: {e}")

    def _get_value(
        self,
        name: str,
        arg_value: Any,
        env_var: Optional[str],
        type_func = None
    ) -> Any:
        """Get value with priority: arg > env > config file > default."""
        # Priority 1: Function argument
        if arg_value is not None:
            logger.debug(f"Config '{name}' from function argument")
            return arg_value

        # Priority 2: Environment variable
        if env_var and env_var in os.environ:
            value = os.environ[env_var]
            logger.debug(f"Config '{name}' from environment variable {env_var}")
            if type_func:
                return type_func(value)
            return value

        # Priority 3: Config file
        if name in self._config_file_values and self._config_file_values[name] is not None:
            logger.debug(f"Config '{name}' from config file")
            return self._config_file_values[name]

        # Priority 4: Default
        return self.DEFAULTS.get(name)

    def _validate(self):
        """Validate configuration and raise ConfigError if invalid."""
        errors = []
        suggestions = []

        # Check required values
        if not self.password:
            errors.append("Password is required")
            suggestions.append(
                f"Set password via:\n"
                f"  1. Environment variable: {ENV_PASSWORD}=your_password\n"
                f"  2. Function argument: PortfolioManager_API(password='...')\n"
                f"  3. Config file [auth] section (not recommended for security)"
            )

        if not self.username:
            errors.append("Username is required")

        # Validate types
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            errors.append(f"Invalid port: {self.port} (must be 1-65535)")

        if self.timeout and (not isinstance(self.timeout, int) or self.timeout <= 0):
            errors.append(f"Invalid timeout: {self.timeout}")

        # Log warnings
        for warning in self._warnings:
            logger.warning(warning)

        # Raise if errors
        if errors:
            msg = "Configuration errors:\n  - " + "\n  - ".join(errors)
            suggestion = "\n\n".join(suggestions) if suggestions else None
            raise ConfigError(msg, suggestion)

    @property
    def base_url(self) -> str:
        """Get full base URL."""
        return f"http://{self.host}:{self.port}"

    def __repr__(self) -> str:
        return (
            f"Config(host='{self.host}', port={self.port}, "
            f"username='{self.username}', timeout={self.timeout})"
        )

    def to_dict(self, mask_password: bool = True) -> Dict[str, Any]:
        """Export config as dictionary (for debugging)."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": "***" if mask_password and self.password else self.password,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "base_url": self.base_url,
            "token_refresh_buffer": self.token_refresh_buffer,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }
