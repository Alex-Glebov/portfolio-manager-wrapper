"""
Authentication tests using PortfolioManager_API wrapper
Tests: login, connection, error handling
"""
import pytest
from portfolio_manager_wrapper import (
    PortfolioManager_API,
    AuthenticationError,
    ConnectionError,
)


class TestAuthentication:
    """Test authentication using wrapper"""

    def test_login_with_valid_credentials(self, cli_host, cli_port):
        """Login with valid credentials should work"""
        api = PortfolioManager_API(
            host=cli_host,
            port=cli_port,
            username="admin",
            password="admin",
            auto_login=False
        )
        api.connect()
        assert api.is_connected
        api.disconnect()

    def test_login_with_invalid_credentials(self, cli_host, cli_port):
        """Login with invalid credentials should fail"""
        api = PortfolioManager_API(
            host=cli_host,
            port=cli_port,
            username="invalid",
            password="wrong",
            auto_login=False
        )
        with pytest.raises(AuthenticationError):
            api.connect()

    def test_auto_login_on_request(self, cli_host, cli_port):
        """Should auto-login on first request if auto_login=True"""
        api = PortfolioManager_API(
            host=cli_host,
            port=cli_port,
            username="admin",
            password="admin",
            auto_login=True
        )
        # Should not need explicit connect()
        version = api.get_version()
        assert "version" in version
        assert api.is_connected
        api.disconnect()

    def test_connection_refused_wrong_port(self, cli_host):
        """Should raise ConnectionError for wrong port"""
        api = PortfolioManager_API(
            host=cli_host,
            port=12345,  # Wrong port
            username="admin",
            password="admin",
            auto_login=False
        )
        with pytest.raises(ConnectionError):
            api.connect()


class TestClientProperties:
    """Test wrapper client properties"""

    def test_base_url_property(self, api_client):
        """Should expose base_url"""
        assert api_client.base_url is not None
        assert api_client.base_url.startswith("http://")

    def test_is_connected_property(self, api_client):
        """Should expose is_connected"""
        assert api_client.is_connected is True

    def test_context_manager(self, cli_host, cli_port):
        """Should work with context manager"""
        with PortfolioManager_API(
            host=cli_host,
            port=cli_port,
            username="admin",
            password="admin"
        ) as api:
            assert api.is_connected
            version = api.get_version()
            assert "version" in version


class TestHealthAndVersion:
    """Test health and version endpoints"""

    def test_health_check(self, api_client):
        """Health check should return status"""
        health = api_client.health_check()
        assert health["status"] == "healthy"
        assert "transactions_count" in health
        assert "timestamp" in health

    def test_get_version(self, api_client):
        """Should return version info"""
        version = api_client.get_version()
        assert "version" in version
        assert "service" in version
        # Verify version is a valid semantic version string
        ver = version["version"]
        assert isinstance(ver, str)
        assert len(ver.split('.')) >= 2
