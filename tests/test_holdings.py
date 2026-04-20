"""
Holdings and Portfolio tests using PortfolioManager_API wrapper
Tests: Portfolio calculations, holdings summary
"""
import pytest
import uuid


class TestHoldings:
    """Test holdings calculations using wrapper"""

    def test_get_holdings_returns_list(self, api_client):
        """Should return list of holdings"""
        holdings = api_client.get_holdings()
        assert isinstance(holdings, list)

    def test_get_specific_holding(self, api_client):
        """Should get holding for specific item"""
        unique_name = f"TestSteel_{uuid.uuid4().hex[:8]}"

        # Get existing balance first (handles CSV persistence)
        try:
            initial = api_client.get_holding(unique_name)
            initial_balance = initial.get("current_balance", 0)
        except Exception:
            initial_balance = 0

        # Create a transaction
        txn = {
            "name": unique_name,
            "cost": 50.0,
            "qty": 100,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "TEST",
            "notes": ""
        }
        api_client.create_transaction(**txn)

        # Verify balance increased by 100
        result = api_client.get_holding(unique_name)
        assert result["name"] == unique_name
        assert result["current_balance"] == initial_balance + 100

    def test_get_nonexistent_holding(self, api_client):
        """Should raise APIError for nonexistent holding"""
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            api_client.get_holding("NONEXISTENT_ITEM_12345")
        assert exc_info.value.status_code == 404


class TestPortfolioSummary:
    """Test portfolio summary using wrapper"""

    def test_get_portfolio_summary(self, api_client):
        """Should return portfolio summary"""
        summary = api_client.get_portfolio_summary()
        assert "total_transactions" in summary
        assert "total_unique_items" in summary
        assert "total_value_in_portfolio" in summary
        assert "items" in summary
        assert isinstance(summary["items"], list)

    def test_portfolio_summary_calculations(self, api_client):
        """Summary should reflect actual transactions"""
        import uuid

        # Create some transactions
        for i in range(3):
            txn = {
                "name": f"SummaryItem_{uuid.uuid4().hex[:8]}_{i}",
                "cost": 10.0 + i,
                "qty": 10,
                "cost_units": "USD",
                "direction": "in",
                "counterpart_id": "TEST",
                "notes": ""
            }
            api_client.create_transaction(**txn)

        summary = api_client.get_portfolio_summary()
        assert summary["total_unique_items"] >= 3
        assert summary["total_transactions"] >= 3


class TestCounterpartHistory:
    """Test counterpart history using wrapper"""

    def test_get_counterpart_history(self, api_client):
        """Should return history for counterpart"""
        unique_counterpart = f"HISTORY_TEST_{uuid.uuid4().hex[:8]}"

        # Create transactions with same counterpart
        for _ in range(2):
            txn = {
                "name": f"HistoryItem_{uuid.uuid4().hex[:8]}",
                "cost": 25.0,
                "qty": 10,
                "cost_units": "USD",
                "direction": "in",
                "counterpart_id": unique_counterpart,
                "notes": ""
            }
            api_client.create_transaction(**txn)

        result = api_client.get_counterpart_history(unique_counterpart)
        assert result["counterpart_id"] == unique_counterpart
        assert "transaction_count" in result
        assert "total_quantity_in" in result
        assert "total_quantity_out" in result
        assert "net_flow" in result
        assert "transactions" in result
