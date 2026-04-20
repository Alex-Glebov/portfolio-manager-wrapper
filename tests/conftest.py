"""
Pytest configuration and fixtures for Portfolio Manager Wrapper tests

These tests use the wrapper classes instead of direct HTTP calls
"""
import os
import sys
import pytest
import asyncio

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from portfolio_manager_wrapper import PortfolioManager_API, PortfolioManager_API_Async


# =============================================================================
# Pytest CLI Arguments
# =============================================================================

def pytest_addoption(parser):
    """Add CLI options for test configuration"""
    parser.addoption(
        '--host',
        action='store',
        default=os.getenv('API_HOST', 'localhost'),
        help='API server host (default: localhost or API_HOST env var)'
    )
    parser.addoption(
        '--port',
        action='store',
        default=os.getenv('API_PORT', '8000'),
        help='API server port (default: 8000 or API_PORT env var)'
    )
    parser.addoption(
        '--username',
        action='store',
        default=os.getenv('TEST_USERNAME', 'admin'),
        help='Test username (default: admin or TEST_USERNAME env var)'
    )
    parser.addoption(
        '--password',
        action='store',
        default=os.getenv('TEST_PASSWORD', 'admin'),
        help='Test password (default: admin or TEST_PASSWORD env var)'
    )


@pytest.fixture(scope="session")
def cli_host(request):
    """Get host from CLI or env"""
    return request.config.getoption('--host')


@pytest.fixture(scope="session")
def cli_port(request):
    """Get port from CLI or env"""
    return int(request.config.getoption('--port'))


@pytest.fixture(scope="session")
def cli_username(request):
    """Get username from CLI or env"""
    return request.config.getoption('--username')


@pytest.fixture(scope="session")
def cli_password(request):
    """Get password from CLI or env"""
    return request.config.getoption('--password')


# =============================================================================
# Wrapper Client Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def api_client(cli_host, cli_port, cli_username, cli_password):
    """Create synchronous wrapper client for API tests"""
    print(f"\n>>> Testing against API: http://{cli_host}:{cli_port}")
    client = PortfolioManager_API(
        host=cli_host,
        port=cli_port,
        username=cli_username,
        password=cli_password,
        auto_login=False
    )
    client.connect()
    yield client
    client.disconnect()


@pytest.fixture
async def async_api_client(cli_host, cli_port, cli_username, cli_password):
    """Create asynchronous wrapper client for API tests"""
    client = PortfolioManager_API_Async(
        host=cli_host,
        port=cli_port,
        username=cli_username,
        password=cli_password,
        auto_login=False
    )
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
def sample_transaction():
    """Return sample transaction data"""
    import uuid
    return {
        "name": f"TestItem_{uuid.uuid4().hex[:8]}",
        "cost": 10.50,
        "qty": 100,
        "cost_units": "USD",
        "direction": "in",
        "counterpart_id": "TEST_SUPPLIER",
        "notes": "Test transaction"
    }


@pytest.fixture(autouse=True)
def log_test_start(request):
    """Log test start"""
    print(f"\n>>> Running test: {request.node.name}")


# =============================================================================
# Version Compatibility Fixture
# =============================================================================

@pytest.fixture(scope="session")
def require_v0_2_0(api_client):
    """Skip tests if server version is below 0.2.0"""
    from packaging import version

    try:
        version_info = api_client.get_version()
        server_version = version_info.get("version", "0.0.0")
    except Exception:
        pytest.skip("Cannot determine server version - server unreachable")

    try:
        parsed_version = version.parse(server_version)
        min_version = version.parse("0.2.0")
    except Exception:
        pytest.skip(f"Cannot parse server version: {server_version}")

    if parsed_version < min_version:
        pytest.skip(
            f"Server version {server_version} < 0.2.0. "
            f"Multi-portfolio feature not available."
        )
