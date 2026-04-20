"""
Version compatibility tests using PortfolioManager_API wrapper
Tests: Server version check, API compatibility
"""
import pytest
import re
from packaging import version


class TestVersionCompatibility:
    """Test server version compatibility using wrapper"""

    def test_server_version_is_0_2_0_or_higher(self, api_client):
        """Server should be version 0.2.0 or higher for multi-portfolio support"""
        version_info = api_client.get_version()
        assert "version" in version_info, "Response should contain version field"

        server_version = version_info["version"]
        assert isinstance(server_version, str), "Version should be a string"

        # Parse version string (handles versions like "0.2.0", "0.2.1", "0.3.0")
        try:
            parsed_version = version.parse(server_version)
            min_version = version.parse("0.2.0")
        except Exception as e:
            pytest.fail(f"Could not parse version '{server_version}': {e}")

        assert parsed_version >= min_version, (
            f"Server version {server_version} is too old. "
            f"Multi-portfolio tests require version 0.2.0 or higher. "
            f"Please upgrade portfolio-manager."
        )

    def test_version_format_is_semantic(self, api_client):
        """Version should follow semantic versioning format"""
        version_info = api_client.get_version()
        server_version = version_info["version"]

        # Basic semver pattern: major.minor.patch (e.g., 0.2.0)
        semver_pattern = r'^\d+\.\d+\.\d+([\-\+].*)?$'
        assert re.match(semver_pattern, server_version), (
            f"Version '{server_version}' does not follow semantic versioning"
        )

    def test_health_endpoint_returns_version_info(self, api_client):
        """Health endpoint should indicate server is ready"""
        health = api_client.health_check()
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "transactions_count" in health


class TestWrapperVersion:
    """Test wrapper version compatibility"""

    def test_wrapper_has_version(self):
        """Wrapper should expose version"""
        from portfolio_manager_wrapper import __version__
        assert isinstance(__version__, str)
        assert len(__version__.split('.')) >= 2

    def test_wrapper_version_compatibility(self, api_client):
        """Wrapper should work with server version"""
        from portfolio_manager_wrapper import __min_api_version__, __max_api_version__

        version_info = api_client.get_version()
        server_version = version_info["version"]

        parsed_server = version.parse(server_version)
        parsed_min = version.parse(__min_api_version__)
        parsed_max = version.parse(__max_api_version__)

        assert parsed_min <= parsed_server <= parsed_max, (
            f"Server version {server_version} not in wrapper compatibility range "
            f"{__min_api_version__} - {__max_api_version__}"
        )
