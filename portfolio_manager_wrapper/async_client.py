"""
Asynchronous API client for Portfolio Manager.

Usage:
    from portfolio_manager_wrapper import PortfolioManager_API_Async

    # Using async context manager (recommended)
    async with PortfolioManager_API_Async() as api:
        transactions = await api.get_transactions()

    # Or manual management
    api = PortfolioManager_API_Async()
    await api.connect()
    transactions = await api.get_transactions()
    await api.disconnect()
"""

import logging
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

import httpx

from .config import Config
from .async_auth import AsyncTokenManager
from .exceptions import (
    PortfolioManagerError,
    AuthenticationError,
    ConnectionError,
    APIError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class PortfolioManager_API_Async:
    """Asynchronous client for Portfolio Manager API.

    Provides convenient interface with:
    - Automatic authentication
    - Token refresh
    - Portfolio support
    - Comprehensive error handling
    - Logging

    Configuration priority:
    1. Constructor arguments
    2. Environment variables
    3. Config file
    4. Default values

    Args:
        config_path: Path to config file
        host: API server host
        port: API server port
        username: Login username
        password: Login password (prefer env var)
        timeout: Request timeout in seconds
        portfolio: Default portfolio to use (optional)
        auto_login: Automatically login on first request
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None,
        portfolio: Optional[str] = None,
        auto_login: bool = True,
    ):
        """Initialize async API client."""
        # Setup logging first
        self._setup_logging()
        logger.info("=" * 60)
        logger.info("Portfolio Manager API Wrapper Starting (Async)")
        logger.info("=" * 60)

        # Load configuration
        try:
            self.config = Config(
                config_path=config_path,
                host=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
            )
            logger.info(f"Configuration loaded: {self.config}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

        # Initialize components
        self._token_manager = AsyncTokenManager(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._default_portfolio = portfolio
        self._auto_login = auto_login
        self._connected = False

        logger.info(f"Async API Wrapper initialized for {self.config.base_url}")

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def connect(self) -> "PortfolioManager_API_Async":
        """Connect to API and authenticate.

        Returns:
            self for method chaining

        Raises:
            AuthenticationError: If login fails
            ConnectionError: If cannot connect to server
        """
        if self._connected:
            logger.debug("Already connected")
            return self

        logger.info(f"Connecting to {self.config.base_url}...")

        try:
            # Create HTTP client
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

            # Authenticate
            await self._token_manager.login(
                self.config.username,
                self.config.password,
            )

            self._connected = True
            logger.info("Successfully connected to API")

            return self

        except Exception:
            self._client = None
            raise

    async def disconnect(self):
        """Disconnect from API and cleanup."""
        if self._client:
            logger.info("Disconnecting from API...")
            await self._client.aclose()
            self._client = None

        await self._token_manager.clear_token()
        self._connected = False
        logger.info("Disconnected from API")

    async def __aenter__(self) -> "PortfolioManager_API_Async":
        """Async context manager entry."""
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False

    async def _ensure_connected(self):
        """Ensure we have a valid connection."""
        if not self._connected and self._auto_login:
            await self.connect()

        if not self._client:
            raise ConnectionError(
                "Not connected to API. Call connect() first or use context manager."
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        portfolio: Optional[str] = None,
    ) -> Any:
        """Make authenticated request to API."""
        await self._ensure_connected()

        # Build headers
        headers = await self._token_manager.get_auth_header()
        if json_data:
            headers["Content-Type"] = "application/json"

        # Add portfolio header if specified
        effective_portfolio = portfolio or self._default_portfolio
        if effective_portfolio:
            headers["X-Portfolio"] = effective_portfolio
            logger.debug(f"Using portfolio: '{effective_portfolio}'")

        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"

        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=headers,
            )

            # Handle token expiry
            if response.status_code == 401:
                logger.warning("Token expired, attempting refresh...")
                await self._token_manager.ensure_token()

                # Retry with new token
                headers = await self._token_manager.get_auth_header()
                if effective_portfolio:
                    headers["X-Portfolio"] = effective_portfolio

                response = await self._client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers,
                )

            response.raise_for_status()

            if response.status_code == 204:
                return None

            return response.json() if response.text else None

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to API: {e}",
                {"base_url": self.config.base_url}
            )
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"API error {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.text else {}
            )

    # ==================== Public API Methods ====================

    async def get_version(self) -> Dict[str, Any]:
        """Get API version information.

        Returns:
            Dict with service, version, description, auth_enabled
        """
        await self._ensure_connected()

        try:
            response = await self._client.get("/")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Failed to get version: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check API health.

        Returns:
            Dict with status, timestamp, transactions_count
        """
        await self._ensure_connected()

        try:
            response = await self._client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Health check failed: {e}")

    # Transactions
    async def create_transaction(
        self,
        name: str,
        cost: float,
        qty: float,
        cost_units: str,
        direction: str,
        counterpart_id: str,
        notes: Optional[str] = None,
        portfolio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new transaction.

        Args:
            name: Item name
            cost: Cost per unit
            qty: Quantity
            cost_units: Currency/unit type (e.g., USD, EUR)
            direction: "in" or "out"
            counterpart_id: Source/destination ID
            notes: Optional notes
            portfolio: Portfolio to create in (optional)

        Returns:
            Created transaction dict with id and timestamp
        """
        if direction not in ("in", "out"):
            raise ValidationError(f"Direction must be 'in' or 'out', got '{direction}'")

        data = {
            "name": name,
            "cost": cost,
            "qty": qty,
            "cost_units": cost_units,
            "direction": direction,
            "counterpart_id": counterpart_id,
            "notes": notes,
        }

        logger.info(f"Creating transaction: {name} {direction} {qty} {cost_units}")
        return await self._request("POST", "/transactions", json_data=data, portfolio=portfolio)

    async def get_transactions(
        self,
        name: Optional[str] = None,
        direction: Optional[str] = None,
        counterpart_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        portfolio: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering.

        Args:
            name: Filter by item name
            direction: Filter by direction ("in" or "out")
            counterpart_id: Filter by counterpart
            limit: Max results (1-1000)
            offset: Pagination offset
            portfolio: Portfolio to query (optional)

        Returns:
            List of transaction dicts
        """
        params = {"limit": limit, "offset": offset}
        if name:
            params["name"] = name
        if direction:
            params["direction"] = direction
        if counterpart_id:
            params["counterpart_id"] = counterpart_id

        logger.debug(f"Fetching transactions with params: {params}")
        return await self._request("GET", "/transactions", params=params, portfolio=portfolio)

    async def get_transaction(self, transaction_id: int, portfolio: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific transaction by ID.

        Args:
            transaction_id: Transaction ID
            portfolio: Portfolio to query (optional)

        Returns:
            Transaction dict

        Raises:
            APIError: If transaction not found (404)
        """
        return await self._request("GET", f"/transactions/{transaction_id}", portfolio=portfolio)

    async def update_transaction(
        self,
        transaction_id: int,
        updates: Dict[str, Any],
        portfolio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing transaction.

        Args:
            transaction_id: Transaction ID to update
            updates: Dict of fields to update
            portfolio: Portfolio to update in (optional)

        Returns:
            Updated transaction dict
        """
        logger.info(f"Updating transaction {transaction_id}: {updates}")
        return await self._request(
            "PUT",
            f"/transactions/{transaction_id}",
            json_data=updates,
            portfolio=portfolio,
        )

    async def delete_transaction(self, transaction_id: int, portfolio: Optional[str] = None) -> bool:
        """Delete a transaction.

        Args:
            transaction_id: Transaction ID to delete
            portfolio: Portfolio to delete from (optional)

        Returns:
            True if deleted successfully

        Raises:
            APIError: If transaction not found (404)
        """
        logger.info(f"Deleting transaction {transaction_id}")
        await self._request("DELETE", f"/transactions/{transaction_id}", portfolio=portfolio)
        return True

    # Holdings
    async def get_holdings(
        self,
        name: Optional[str] = None,
        portfolio: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get portfolio holdings.

        Args:
            name: Filter by specific item name
            portfolio: Portfolio to query (optional)

        Returns:
            List of holding summaries
        """
        params = {}
        if name:
            params["name"] = name

        return await self._request("GET", "/holdings", params=params, portfolio=portfolio)

    async def get_holding(self, item_name: str, portfolio: Optional[str] = None) -> Dict[str, Any]:
        """Get holdings for a specific item.

        Args:
            item_name: Item name
            portfolio: Portfolio to query (optional)

        Returns:
            Holding summary dict
        """
        return await self._request("GET", f"/holdings/{item_name}", portfolio=portfolio)

    async def get_portfolio_summary(self, portfolio: Optional[str] = None) -> Dict[str, Any]:
        """Get overall portfolio statistics.

        Args:
            portfolio: Portfolio to query (optional)

        Returns:
            Portfolio summary with total_transactions, total_unique_items, etc.
        """
        return await self._request("GET", "/portfolio/summary", portfolio=portfolio)

    async def get_counterpart_history(
        self,
        counterpart_id: str,
        portfolio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get transaction history with a specific counterpart.

        Args:
            counterpart_id: Counterpart ID
            portfolio: Portfolio to query (optional)

        Returns:
            Dict with transaction history and totals
        """
        return await self._request(
            "GET",
            f"/portfolio/counterpart/{counterpart_id}/history",
            portfolio=portfolio,
        )

    # Exports
    async def export_transactions(
        self,
        save_path: Optional[str] = None,
        portfolio: Optional[str] = None,
    ) -> bytes:
        """Export transactions to CSV.

        Args:
            save_path: If provided, save to file and return bytes
            portfolio: Portfolio to export (optional)

        Returns:
            CSV file content as bytes
        """
        await self._ensure_connected()

        headers = await self._token_manager.get_auth_header()
        if portfolio:
            headers["X-Portfolio"] = portfolio

        response = await self._client.get(
            "/export/transactions",
            headers=headers,
        )
        response.raise_for_status()

        content = response.content

        if save_path:
            with open(save_path, "wb") as f:
                f.write(content)
            logger.info(f"Transactions exported to {save_path}")

        return content

    async def export_holdings(
        self,
        save_path: Optional[str] = None,
        portfolio: Optional[str] = None,
    ) -> bytes:
        """Export holdings to CSV.

        Args:
            save_path: If provided, save to file and return bytes
            portfolio: Portfolio to export (optional)

        Returns:
            CSV file content as bytes
        """
        await self._ensure_connected()

        headers = await self._token_manager.get_auth_header()
        if portfolio:
            headers["X-Portfolio"] = portfolio

        response = await self._client.get(
            "/export/holdings",
            headers=headers,
        )
        response.raise_for_status()

        content = response.content

        if save_path:
            with open(save_path, "wb") as f:
                f.write(content)
            logger.info(f"Holdings exported to {save_path}")

        return content

    # Properties
    @property
    def is_connected(self) -> bool:
        """Check if connected to API."""
        return self._connected

    @property
    def base_url(self) -> str:
        """Get API base URL."""
        return self.config.base_url

    @property
    def current_portfolio(self) -> Optional[str]:
        """Get current default portfolio."""
        return self._default_portfolio

    def set_default_portfolio(self, portfolio: Optional[str]):
        """Set default portfolio for subsequent requests."""
        self._default_portfolio = portfolio
        logger.info(f"Default portfolio set to: '{portfolio}'")
