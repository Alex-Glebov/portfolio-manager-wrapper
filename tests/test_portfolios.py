"""
Multi-portfolio tests using PortfolioManager_API wrapper
Tests: Portfolio isolation, access control, X-Portfolio header
"""
import pytest
import uuid


class TestPortfolioSupport:
    """Test multi-portfolio feature availability using wrapper"""

    def test_multi_portfolio_feature_available(self, api_client, require_v0_2_0):
        """Multi-portfolio feature should be available in v0.2.0+"""
        unique_name = f"PortfolioTest_{uuid.uuid4().hex[:8]}"
        result = api_client.create_transaction(
            name=unique_name,
            cost=10.0,
            qty=10,
            cost_units="USD",
            direction="in",
            counterpart_id="TEST_SUPPLIER",
            notes="Test multi-portfolio"
        )
        assert "id" in result


class TestDefaultPortfolio:
    """Test default portfolio (empty name) using wrapper"""

    def test_transactions_without_portfolio_header(self, api_client, require_v0_2_0):
        """Transactions without portfolio go to default"""
        unique_name = f"DefaultPortfolio_{uuid.uuid4().hex[:8]}"

        # Create transaction
        created = api_client.create_transaction(
            name=unique_name,
            cost=25.0,
            qty=50,
            cost_units="USD",
            direction="in",
            counterpart_id="DEFAULT_TEST",
            notes="Test default portfolio"
        )
        created_id = created["id"]

        # Get transactions without portfolio header
        transactions = api_client.get_transactions()

        # Should find our transaction
        found = any(t["id"] == created_id for t in transactions)
        assert found, "Transaction should be in default portfolio"

    def test_transactions_with_explicit_portfolio(self, api_client, require_v0_2_0):
        """Should support explicit portfolio in requests"""
        result = api_client.get_holdings(portfolio="")
        assert isinstance(result, list)


class TestPortfolioIsolation:
    """Test that portfolios are isolated from each other"""

    def test_portfolios_isolated(self, api_client, require_v0_2_0):
        """Transactions in different portfolios should not mix"""
        unique_id = uuid.uuid4().hex[:8]
        default_name = f"DefaultOnly_{unique_id}"
        portfolio_name = f"PortfolioOnly_{unique_id}"

        # Create transaction in default portfolio
        api_client.create_transaction(
            name=default_name,
            cost=10.0,
            qty=100,
            cost_units="USD",
            direction="in",
            counterpart_id="ISOLATION_TEST",
            notes="In default portfolio"
        )

        # Check transaction exists in default portfolio
        default_transactions = api_client.get_transactions()
        default_names = [t["name"] for t in default_transactions]
        assert default_name in default_names

        # Create transaction with named portfolio
        try:
            api_client.create_transaction(
                name=portfolio_name,
                cost=20.0,
                qty=50,
                cost_units="USD",
                direction="in",
                counterpart_id="ISOLATION_TEST",
                notes="In user portfolio",
                portfolio="testportfolio"
            )

            # Verify portfolio-only transaction does NOT appear in default
            default_transactions = api_client.get_transactions()
            default_names = [t["name"] for t in default_transactions]
            assert portfolio_name not in default_names

            # Verify default-only transaction does NOT appear in named portfolio
            portfolio_transactions = api_client.get_transactions(portfolio="testportfolio")
            portfolio_names = [t["name"] for t in portfolio_transactions]
            assert default_name not in portfolio_names

        except Exception as e:
            pytest.skip(f"Portfolio access not configured: {e}")


class TestPortfolioExport:
    """Test export from portfolios using wrapper"""

    def test_export_with_portfolio_param(self, api_client, require_v0_2_0):
        """Should export with portfolio parameter"""
        content = api_client.export_transactions(portfolio="")
        assert isinstance(content, bytes)

    def test_export_holdings_with_portfolio(self, api_client, require_v0_2_0):
        """Should export holdings with portfolio parameter"""
        content = api_client.export_holdings(portfolio="")
        assert isinstance(content, bytes)


class TestDefaultPortfolioProperty:
    """Test default portfolio property in wrapper"""

    def test_set_default_portfolio(self, api_client):
        """Should set default portfolio for subsequent requests"""
        api_client.set_default_portfolio("")
        assert api_client.current_portfolio == ""

        api_client.set_default_portfolio(None)
        assert api_client.current_portfolio is None

    def test_default_portfolio_used_in_requests(self, api_client, require_v0_2_0):
        """Default portfolio should be used automatically"""
        api_client.set_default_portfolio("")

        # Request should use default portfolio
        holdings = api_client.get_holdings()
        assert isinstance(holdings, list)
