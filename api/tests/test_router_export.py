"""Tests for the /api/export router and ExportService."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_export_service
from app.services.export_service import ExportService

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_EXPORT_TX = {
    "id": "tx-export-001",
    "date": "2026-04-10",
    "valueDate": "2026-04-10",
    "accountId": "acc-001",
    "bankDescription": "Donation",
    "categoryId": "cat-001",
    "subcategoryId": "subcat-001",
    "tagIds": ["tag-001"],
    "amount": 150.50,
    "currency": "EUR",
    "balance": 1000.00,
    "detail": "Spring campaign",
    "movementNumber": "MV-001",
    "branchNumber": "BR-01",
}


# ---------------------------------------------------------------------------
# GET /api/export/transactions
# ---------------------------------------------------------------------------


class TestExportTransactionsRouter:
    async def test_returns_xlsx_file(self, admin_client):
        mock_svc = AsyncMock()
        mock_svc.export_transactions_xlsx.return_value = b"PK\x03\x04fake-xlsx-bytes"
        app.dependency_overrides[get_export_service] = lambda: mock_svc

        response = await admin_client.get("/api/export/transactions?dateFrom=2026-04-01&dateTo=2026-04-30")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "movimientos_2026-04-01_2026-04-30.xlsx" in response.headers["content-disposition"]

    async def test_missing_params_returns_422(self, admin_client):
        mock_svc = AsyncMock()
        app.dependency_overrides[get_export_service] = lambda: mock_svc

        response = await admin_client.get("/api/export/transactions")

        assert response.status_code == 422

    async def test_with_optional_filters(self, admin_client):
        mock_svc = AsyncMock()
        mock_svc.export_transactions_xlsx.return_value = b"PK\x03\x04xlsx"
        app.dependency_overrides[get_export_service] = lambda: mock_svc

        response = await admin_client.get(
            "/api/export/transactions" "?dateFrom=2026-01-01&dateTo=2026-12-31" "&accountId=acc-001&categoryId=cat-001"
        )

        assert response.status_code == 200
        mock_svc.export_transactions_xlsx.assert_called_once_with(
            date_from=date(2026, 1, 1),
            date_to=date(2026, 12, 31),
            account_id="acc-001",
            category_id="cat-001",
        )


# ---------------------------------------------------------------------------
# ExportService unit tests
# ---------------------------------------------------------------------------


class TestExportService:
    @pytest.fixture
    def mock_txn_service(self):
        svc = AsyncMock()
        svc.get_transactions_for_export.return_value = [SAMPLE_EXPORT_TX]
        return svc

    @pytest.fixture
    def export_service(self, mock_txn_service):
        return ExportService(transaction_service=mock_txn_service)

    async def test_returns_bytes(self, export_service, mock_txn_service):
        result = await export_service.export_transactions_xlsx(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )

        assert isinstance(result, bytes)
        # XLSX files start with PK (zip magic)
        assert result[:2] == b"PK"

    async def test_calls_transaction_service(self, export_service, mock_txn_service):
        await export_service.export_transactions_xlsx(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            account_id="acc-001",
            category_id="cat-001",
        )

        mock_txn_service.get_transactions_for_export.assert_awaited_once_with(
            date_from="2026-04-01",
            date_to="2026-04-30",
            account_id="acc-001",
            category_id="cat-001",
        )

    async def test_empty_transactions(self, mock_txn_service):
        mock_txn_service.get_transactions_for_export.return_value = []
        svc = ExportService(transaction_service=mock_txn_service)

        result = await svc.export_transactions_xlsx(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )

        assert isinstance(result, bytes)
        assert result[:2] == b"PK"

    async def test_multiple_transactions(self, mock_txn_service):
        """Test with more than 50 rows (balance auto-size loop limit)."""
        many_txs = [{**SAMPLE_EXPORT_TX, "id": f"tx-{i}", "tagIds": [], "balance": None} for i in range(60)]
        mock_txn_service.get_transactions_for_export.return_value = many_txs
        svc = ExportService(transaction_service=mock_txn_service)

        result = await svc.export_transactions_xlsx(
            date_from=date(2026, 1, 1),
            date_to=date(2026, 12, 31),
        )

        assert isinstance(result, bytes)

    async def test_transaction_with_none_fields(self, mock_txn_service):
        """Ensure None optional fields don't cause errors."""
        tx = {
            "id": "tx-minimal",
            "date": "2026-04-10",
            "valueDate": None,
            "accountId": None,
            "bankDescription": None,
            "categoryId": None,
            "subcategoryId": None,
            "tagIds": None,
            "amount": 50.0,
            "currency": None,
            "balance": None,
            "detail": None,
            "movementNumber": None,
            "branchNumber": None,
        }
        mock_txn_service.get_transactions_for_export.return_value = [tx]
        svc = ExportService(transaction_service=mock_txn_service)

        result = await svc.export_transactions_xlsx(
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )

        assert isinstance(result, bytes)
