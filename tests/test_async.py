"""
Async client tests using PortfolioManager_API_Async
Tests: All async operations mirror sync operations
"""
import pytest
import asyncio
import uuid


class TestAsyncClient:
    """Test async client functionality"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, cli_host, cli_port):
        """Should work with async context manager"""
        from portfolio_manager_wrapper import PortfolioManager_API_Async

        async with PortfolioManager_API_Async(
            host=cli_host,
            port=cli_port,
            username="admin",
            password="admin"
        ) as api:
            assert api.is_connected
            version = await api.get_version()
            assert "version" in version

    @pytest.mark.asyncio
    async def test_async_get_transactions(self, async_api_client):
        """Should get transactions asynchronously"""
        transactions = await async_api_client.get_transactions()
        assert isinstance(transactions, list)

    @pytest.mark.asyncio
    async def test_async_create_transaction(self, async_api_client):
        """Should create transaction asynchronously"""
        unique_name = f"AsyncTest_{uuid.uuid4().hex[:8]}"
        result = await async_api_client.create_transaction(
            name=unique_name,
            cost=25.0,
            qty=10,
            cost_units="USD",
            direction="in",
            counterpart_id="ASYNC_TEST",
            notes="Async test transaction"
        )
        assert result["name"] == unique_name
        assert "id" in result

    @pytest.mark.asyncio
    async def test_async_get_transaction(self, async_api_client):
        """Should get single transaction asynchronously"""
        # Create first
        unique_name = f"AsyncGet_{uuid.uuid4().hex[:8]}"
        created = await async_api_client.create_transaction(
            name=unique_name,
            cost=15.0,
            qty=5,
            cost_units="USD",
            direction="in",
            counterpart_id="ASYNC_GET_TEST"
        )
        created_id = created["id"]

        # Get by ID
        result = await async_api_client.get_transaction(created_id)
        assert result["id"] == created_id

    @pytest.mark.asyncio
    async def test_async_update_transaction(self, async_api_client):
        """Should update transaction asynchronously"""
        # Create
        unique_name = f"AsyncUpdate_{uuid.uuid4().hex[:8]}"
        created = await async_api_client.create_transaction(
            name=unique_name,
            cost=20.0,
            qty=10,
            cost_units="USD",
            direction="in",
            counterpart_id="ASYNC_UPDATE_TEST"
        )
        created_id = created["id"]

        # Update
        result = await async_api_client.update_transaction(
            created_id,
            {"notes": "Updated async", "qty": 50}
        )
        assert result["notes"] == "Updated async"
        assert result["qty"] == 50

    @pytest.mark.asyncio
    async def test_async_delete_transaction(self, async_api_client):
        """Should delete transaction asynchronously"""
        # Create
        unique_name = f"AsyncDelete_{uuid.uuid4().hex[:8]}"
        created = await async_api_client.create_transaction(
            name=unique_name,
            cost=10.0,
            qty=5,
            cost_units="USD",
            direction="in",
            counterpart_id="ASYNC_DELETE_TEST"
        )
        created_id = created["id"]

        # Delete
        result = await async_api_client.delete_transaction(created_id)
        assert result is True

        # Verify deleted
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            await async_api_client.get_transaction(created_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_async_get_holdings(self, async_api_client):
        """Should get holdings asynchronously"""
        holdings = await async_api_client.get_holdings()
        assert isinstance(holdings, list)

    @pytest.mark.asyncio
    async def test_async_get_holding(self, async_api_client):
        """Should get specific holding asynchronously"""
        unique_name = f"AsyncHolding_{uuid.uuid4().hex[:8]}"
        await async_api_client.create_transaction(
            name=unique_name,
            cost=100.0,
            qty=50,
            cost_units="USD",
            direction="in",
            counterpart_id="ASYNC_HOLDING_TEST"
        )

        result = await async_api_client.get_holding(unique_name)
        assert result["name"] == unique_name

    @pytest.mark.asyncio
    async def test_async_get_portfolio_summary(self, async_api_client):
        """Should get portfolio summary asynchronously"""
        summary = await async_api_client.get_portfolio_summary()
        assert "total_transactions" in summary
        assert "total_unique_items" in summary

    @pytest.mark.asyncio
    async def test_async_get_counterpart_history(self, async_api_client):
        """Should get counterpart history asynchronously"""
        unique_counterpart = f"ASYNC_HISTORY_{uuid.uuid4().hex[:8]}"
        await async_api_client.create_transaction(
            name=f"AsyncHistory_{uuid.uuid4().hex[:8]}",
            cost=25.0,
            qty=10,
            cost_units="USD",
            direction="in",
            counterpart_id=unique_counterpart
        )

        result = await async_api_client.get_counterpart_history(unique_counterpart)
        assert result["counterpart_id"] == unique_counterpart

    @pytest.mark.asyncio
    async def test_async_export_transactions(self, async_api_client):
        """Should export transactions asynchronously"""
        content = await async_api_client.export_transactions()
        assert isinstance(content, bytes)

    @pytest.mark.asyncio
    async def test_async_export_holdings(self, async_api_client):
        """Should export holdings asynchronously"""
        content = await async_api_client.export_holdings()
        assert isinstance(content, bytes)

    @pytest.mark.asyncio
    async def test_async_health_check(self, async_api_client):
        """Should check health asynchronously"""
        health = await async_api_client.health_check()
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_async_get_version(self, async_api_client):
        """Should get version asynchronously"""
        version = await async_api_client.get_version()
        assert "version" in version
