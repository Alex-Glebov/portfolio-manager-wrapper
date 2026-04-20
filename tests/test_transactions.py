"""
Transaction CRUD tests using PortfolioManager_API wrapper
Tests: create, read, update, delete transactions
"""
import pytest
import uuid


class TestTransactionCreation:
    """Test creating transactions using wrapper"""

    def test_create_transaction_in(self, api_client, sample_transaction):
        """Should create incoming transaction"""
        result = api_client.create_transaction(**sample_transaction)
        assert result["name"] == sample_transaction["name"]
        assert result["direction"] == "in"
        assert result["qty"] == sample_transaction["qty"]
        assert "id" in result
        assert "timestamp" in result

    def test_create_transaction_out(self, api_client, sample_transaction):
        """Should create outgoing transaction"""
        txn_data = {
            **sample_transaction,
            "name": f"Out_{sample_transaction['name']}",
            "direction": "out",
            "counterpart_id": "TEST_CUSTOMER"
        }
        result = api_client.create_transaction(**txn_data)
        assert result["direction"] == "out"

    def test_create_transaction_calculates_total_value(self, api_client, sample_transaction):
        """Should auto-calculate total_value"""
        result = api_client.create_transaction(**sample_transaction)
        expected = sample_transaction["cost"] * sample_transaction["qty"]
        assert result["total_value"] == expected


class TestTransactionReading:
    """Test reading transactions using wrapper"""

    def test_get_all_transactions(self, api_client):
        """Should return list of transactions"""
        transactions = api_client.get_transactions()
        assert isinstance(transactions, list)

    def test_get_transactions_pagination(self, api_client):
        """Should support pagination"""
        transactions = api_client.get_transactions(limit=5, offset=0)
        assert len(transactions) <= 5

    def test_get_transaction_by_id(self, api_client, sample_transaction):
        """Should get specific transaction by ID"""
        # Create first
        created = api_client.create_transaction(**sample_transaction)
        created_id = created["id"]

        # Get by ID
        result = api_client.get_transaction(created_id)
        assert result["id"] == created_id

    def test_get_nonexistent_transaction(self, api_client):
        """Should raise APIError for nonexistent transaction"""
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            api_client.get_transaction(999999)
        assert exc_info.value.status_code == 404

    def test_filter_transactions_by_name(self, api_client, sample_transaction):
        """Should filter by name"""
        # Create transaction
        api_client.create_transaction(**sample_transaction)

        # Filter by name
        results = api_client.get_transactions(name=sample_transaction["name"])
        assert all(t["name"] == sample_transaction["name"] for t in results)

    def test_filter_transactions_by_direction(self, api_client, sample_transaction):
        """Should filter by direction"""
        results = api_client.get_transactions(direction="in")
        assert all(t["direction"] == "in" for t in results)


class TestTransactionUpdate:
    """Test updating transactions using wrapper"""

    def test_update_transaction(self, api_client, sample_transaction):
        """Should update transaction fields"""
        # Create
        created = api_client.create_transaction(**sample_transaction)
        created_id = created["id"]

        # Update
        updates = {"notes": "Updated notes", "qty": 200}
        result = api_client.update_transaction(created_id, updates)
        assert result["notes"] == "Updated notes"
        assert result["qty"] == 200

    def test_update_nonexistent_transaction(self, api_client):
        """Should raise APIError for nonexistent transaction"""
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            api_client.update_transaction(999999, {"notes": "Update"})
        assert exc_info.value.status_code == 404


class TestTransactionDeletion:
    """Test deleting transactions using wrapper"""

    def test_delete_transaction(self, api_client, sample_transaction):
        """Should delete transaction"""
        # Create
        created = api_client.create_transaction(**sample_transaction)
        created_id = created["id"]

        # Delete
        result = api_client.delete_transaction(created_id)
        assert result is True

        # Verify deleted
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            api_client.get_transaction(created_id)
        assert exc_info.value.status_code == 404

    def test_delete_nonexistent_transaction(self, api_client):
        """Should raise APIError for nonexistent transaction"""
        from portfolio_manager_wrapper import APIError
        with pytest.raises(APIError) as exc_info:
            api_client.delete_transaction(999999)
        assert exc_info.value.status_code == 404
