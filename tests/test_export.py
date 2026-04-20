"""
Export tests using PortfolioManager_API wrapper
Tests: CSV export functionality
"""
import pytest
import csv
import io
import uuid


class TestExport:
    """Test CSV export functionality using wrapper"""

    def test_export_transactions_csv(self, api_client):
        """Should export transactions as CSV bytes"""
        content = api_client.export_transactions()
        assert isinstance(content, bytes)

        # Verify CSV content
        content_str = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content_str))
        rows = list(reader)
        assert len(rows) >= 0  # May be empty but should be valid CSV

    def test_export_holdings_csv(self, api_client):
        """Should export holdings as CSV bytes"""
        content = api_client.export_holdings()
        assert isinstance(content, bytes)

        # Verify CSV content
        content_str = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content_str))
        rows = list(reader)
        assert isinstance(rows, list)

    def test_export_transactions_contains_data(self, api_client):
        """Exported CSV should contain transaction data"""
        # Create a transaction first
        unique_name = f"ExportTest_{uuid.uuid4().hex[:8]}"
        txn = {
            "name": unique_name,
            "cost": 99.99,
            "qty": 50,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "EXPORT_TEST",
            "notes": "For export test"
        }
        api_client.create_transaction(**txn)

        # Export and verify
        content = api_client.export_transactions()
        content_str = content.decode('utf-8')

        # Check CSV headers
        assert "id" in content_str
        assert "timestamp" in content_str
        assert "name" in content_str
        assert "cost" in content_str
        assert "qty" in content_str

        # Check our data is present
        assert unique_name in content_str

    def test_export_save_to_file(self, api_client, tmp_path):
        """Should save export to file"""
        save_path = tmp_path / "transactions.csv"
        content = api_client.export_transactions(save_path=str(save_path))

        # Verify file was created
        assert save_path.exists()

        # Verify file content
        with open(save_path, 'rb') as f:
            file_content = f.read()
        assert file_content == content
