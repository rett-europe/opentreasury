"""Tests for the /api/reports router."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_report_service

# ---------------------------------------------------------------------------
# Sample transaction data for report calculations
# ---------------------------------------------------------------------------

INCOME_TX = {
    "categoryId": "cat-income",
    "accountId": "acc-001",
    "amount": 500.0,
    "month": 4,
    "transactionType": "income",
}

EXPENSE_TX = {
    "categoryId": "cat-expense",
    "accountId": "acc-001",
    "amount": -200.0,
    "month": 4,
    "transactionType": "expense",
}

TRANSFER_TX = {
    "categoryId": None,
    "accountId": "acc-001",
    "amount": 1000.0,
    "month": 4,
    "transactionType": "transfer",
}

REFUND_TX = {
    "categoryId": "cat-expense",
    "accountId": "acc-001",
    "amount": 50.0,
    "month": 4,
    "transactionType": "refund",
}

MIXED_TRANSACTIONS = [INCOME_TX, EXPENSE_TX, TRANSFER_TX, REFUND_TX]


@pytest.fixture
def mock_report_svc():
    return AsyncMock()


@pytest.fixture
def mock_txn_svc():
    svc = AsyncMock()
    svc.get_transactions_for_report.return_value = MIXED_TRANSACTIONS
    return svc


# ---------------------------------------------------------------------------
# GET /api/reports/summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    async def test_calculates_correctly(self, admin_client, mock_report_svc):
        mock_report_svc.get_summary.return_value = {
            "year": 2026,
            "total_income": Decimal("500.00"),
            "total_expense": Decimal("200.00"),
            "net": Decimal("300.00"),
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/summary?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert Decimal(str(data["totalIncome"])) == Decimal("500.00")
        assert Decimal(str(data["totalExpense"])) == Decimal("200.00")
        assert Decimal(str(data["net"])) == Decimal("300.00")

    async def test_empty_transactions(self, admin_client, mock_report_svc):
        mock_report_svc.get_summary.return_value = {
            "year": 2026,
            "total_income": Decimal("0"),
            "total_expense": Decimal("0"),
            "net": Decimal("0"),
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/summary?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert data["totalIncome"] == "0"
        assert data["totalExpense"] == "0"

    async def test_missing_year_returns_422(self, admin_client, mock_report_svc):
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/summary")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/reports/by-category
# ---------------------------------------------------------------------------


class TestGetByCategory:
    async def test_returns_breakdown(self, admin_client, mock_report_svc):
        mock_report_svc.get_by_category.return_value = {
            "year": 2026,
            "month": None,
            "items": [
                {"category_id": "cat-income", "income": Decimal("500"), "expense": Decimal("0"), "net": Decimal("500")},
                {
                    "category_id": "cat-expense",
                    "income": Decimal("0"),
                    "expense": Decimal("200"),
                    "net": Decimal("-200"),
                },
            ],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/by-category?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2

    async def test_with_month_filter(self, admin_client, mock_report_svc):
        mock_report_svc.get_by_category.return_value = {
            "year": 2026,
            "month": 4,
            "items": [],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/by-category?year=2026&month=4")

        assert response.status_code == 200
        data = response.json()
        assert data["month"] == 4


# ---------------------------------------------------------------------------
# GET /api/reports/balance
# ---------------------------------------------------------------------------


class TestGetBalance:
    async def test_returns_balance_breakdown(self, admin_client, mock_report_svc):
        mock_report_svc.get_balance.return_value = {
            "year": 2026,
            "items": [
                {
                    "category_id": "cat-income",
                    "category_name": "Donations",
                    "subcategory_id": "subcat-001",
                    "subcategory_name": "Individuals",
                    "income": Decimal("500"),
                    "expense": Decimal("0"),
                    "net": Decimal("500"),
                },
                {
                    "category_id": "cat-expense",
                    "category_name": "Operations",
                    "subcategory_id": "subcat-002",
                    "subcategory_name": "Rent",
                    "income": Decimal("0"),
                    "expense": Decimal("200"),
                    "net": Decimal("-200"),
                },
            ],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/balance?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert len(data["items"]) == 2
        assert data["items"][0]["categoryId"] == "cat-income"
        assert data["items"][0]["subcategoryName"] == "Individuals"
        assert Decimal(str(data["items"][0]["income"])) == Decimal("500")
        assert Decimal(str(data["items"][1]["expense"])) == Decimal("200")

    async def test_missing_year_returns_422(self, admin_client, mock_report_svc):
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/balance")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/reports/monthly-trend
# ---------------------------------------------------------------------------


class TestGetMonthlyTrend:
    async def test_returns_trend(self, admin_client, mock_report_svc):
        mock_report_svc.get_monthly_trend.return_value = {
            "year": 2026,
            "months": [
                {"month": 3, "income": Decimal("500"), "expense": Decimal("0"), "net": Decimal("500")},
                {"month": 4, "income": Decimal("0"), "expense": Decimal("200"), "net": Decimal("-200")},
            ],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/monthly-trend?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert "months" in data
        assert len(data["months"]) == 2

    async def test_empty_transactions(self, admin_client, mock_report_svc):
        mock_report_svc.get_monthly_trend.return_value = {
            "year": 2026,
            "months": [],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/monthly-trend?year=2026")

        assert response.status_code == 200
        assert response.json()["months"] == []


# ---------------------------------------------------------------------------
# GET /api/reports/by-account
# ---------------------------------------------------------------------------


class TestGetByAccount:
    async def test_returns_account_summary(self, admin_client, mock_report_svc):
        mock_report_svc.get_by_account.return_value = {
            "year": 2026,
            "month": None,
            "items": [
                {
                    "account_id": "acc-001",
                    "total_income": Decimal("500"),
                    "total_expense": Decimal("200"),
                    "net": Decimal("300"),
                    "transaction_count": 2,
                },
            ],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/by-account?year=2026")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["accountId"] == "acc-001"

    async def test_with_month_filter(self, admin_client, mock_report_svc):
        mock_report_svc.get_by_account.return_value = {
            "year": 2026,
            "month": 4,
            "items": [],
        }
        app.dependency_overrides[get_report_service] = lambda: mock_report_svc

        response = await admin_client.get("/api/reports/by-account?year=2026&month=4")

        assert response.status_code == 200
        data = response.json()
        assert data["month"] == 4
