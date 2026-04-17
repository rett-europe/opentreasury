"""Tests for ReportService — transactionType-based classification logic."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.services.report_service import ReportService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_txn_svc():
    return AsyncMock()


@pytest.fixture
def mock_cat_svc():
    svc = AsyncMock()
    svc.list_categories.return_value = [
        {
            "id": "cat-donations",
            "name": "Donations",
            "subcategories": [
                {"id": "subcat-individual", "name": "Individual"},
            ],
        },
        {
            "id": "cat-supplies",
            "name": "Supplies",
            "subcategories": [],
        },
    ]
    return svc


@pytest.fixture
def service(mock_txn_svc, mock_cat_svc):
    return ReportService(transaction_service=mock_txn_svc, category_service=mock_cat_svc)


# ---------------------------------------------------------------------------
# Sample transaction data
# ---------------------------------------------------------------------------

INCOME_TX = {
    "categoryId": "cat-donations",
    "subcategoryId": "subcat-individual",
    "accountId": "acc-001",
    "amount": 500.0,
    "month": 4,
    "transactionType": "income",
}

EXPENSE_TX = {
    "categoryId": "cat-supplies",
    "subcategoryId": None,
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
    "categoryId": "cat-supplies",
    "accountId": "acc-002",
    "amount": 50.0,
    "month": 3,
    "transactionType": "refund",
}

UNCATEGORIZED_INCOME_TX = {
    "categoryId": None,
    "accountId": "acc-001",
    "amount": 75.0,
    "month": 4,
    "transactionType": "income",
}

ALL_TYPES = [INCOME_TX, EXPENSE_TX, TRANSFER_TX, REFUND_TX, UNCATEGORIZED_INCOME_TX]


# ---------------------------------------------------------------------------
# GET /summary — transactionType classification
# ---------------------------------------------------------------------------


class TestGetSummary:
    async def test_income_expense_from_transaction_type(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, EXPENSE_TX]

        result = await service.get_summary(year=2026)

        assert result["total_income"] == Decimal("500")
        assert result["total_expense"] == Decimal("200")
        assert result["net"] == Decimal("300")

    async def test_transfers_excluded_from_totals(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, TRANSFER_TX]

        result = await service.get_summary(year=2026)

        assert result["total_income"] == Decimal("500")
        assert result["total_expense"] == Decimal("0")
        assert result["net"] == Decimal("500")

    async def test_refunds_excluded_from_totals(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [EXPENSE_TX, REFUND_TX]

        result = await service.get_summary(year=2026)

        assert result["total_income"] == Decimal("0")
        assert result["total_expense"] == Decimal("200")
        assert result["net"] == Decimal("-200")

    async def test_all_types_mixed(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = ALL_TYPES

        result = await service.get_summary(year=2026)

        # income: 500 + 75 = 575, expense: 200, transfer/refund excluded
        assert result["total_income"] == Decimal("575")
        assert result["total_expense"] == Decimal("200")
        assert result["net"] == Decimal("375")

    async def test_uses_abs_of_amount(self, service, mock_txn_svc):
        """Expense amounts may be stored negative; abs() ensures correct totals."""
        mock_txn_svc.get_transactions_for_report.return_value = [
            {"amount": -300.0, "transactionType": "expense", "month": 1},
        ]
        result = await service.get_summary(year=2026)
        assert result["total_expense"] == Decimal("300")

    async def test_empty_transactions(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = []

        result = await service.get_summary(year=2026)

        assert result["total_income"] == Decimal("0")
        assert result["total_expense"] == Decimal("0")
        assert result["net"] == Decimal("0")


# ---------------------------------------------------------------------------
# GET /by-category — transactionType + uncategorized bucket
# ---------------------------------------------------------------------------


class TestGetByCategory:
    async def test_groups_by_category(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, EXPENSE_TX]

        result = await service.get_by_category(year=2026)

        items = {item["category_id"]: item for item in result["items"]}
        assert "cat-donations" in items
        assert items["cat-donations"]["income"] == Decimal("500")
        assert "cat-supplies" in items
        assert items["cat-supplies"]["expense"] == Decimal("200")

    async def test_transfers_excluded_from_breakdown(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, TRANSFER_TX]

        result = await service.get_by_category(year=2026)

        # Only income should appear; transfer excluded entirely
        assert len(result["items"]) == 1
        assert result["items"][0]["category_id"] == "cat-donations"

    async def test_refunds_excluded_from_breakdown(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [EXPENSE_TX, REFUND_TX]

        result = await service.get_by_category(year=2026)

        # Only expense should appear; refund excluded
        items = {item["category_id"]: item for item in result["items"]}
        assert len(items) == 1
        assert "cat-supplies" in items
        assert items["cat-supplies"]["expense"] == Decimal("200")

    async def test_uncategorized_bucket_for_null_category(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [UNCATEGORIZED_INCOME_TX]

        result = await service.get_by_category(year=2026)

        items = {item["category_id"]: item for item in result["items"]}
        assert "uncategorized" in items
        assert items["uncategorized"]["income"] == Decimal("75")

    async def test_mixed_with_uncategorized(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [
            INCOME_TX,
            EXPENSE_TX,
            UNCATEGORIZED_INCOME_TX,
        ]

        result = await service.get_by_category(year=2026)

        items = {item["category_id"]: item for item in result["items"]}
        assert len(items) == 3
        assert items["uncategorized"]["income"] == Decimal("75")
        assert items["cat-donations"]["income"] == Decimal("500")
        assert items["cat-supplies"]["expense"] == Decimal("200")

    async def test_respects_month_filter(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = []

        result = await service.get_by_category(year=2026, month=6)

        assert result["month"] == 6
        mock_txn_svc.get_transactions_for_report.assert_awaited_once_with(year=2026, month=6)


# ---------------------------------------------------------------------------
# GET /monthly-trend — transactionType classification
# ---------------------------------------------------------------------------


class TestGetMonthlyTrend:
    async def test_groups_by_month(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, EXPENSE_TX]

        result = await service.get_monthly_trend(year=2026)

        assert len(result["months"]) == 1
        m4 = result["months"][0]
        assert m4["month"] == 4
        assert m4["income"] == Decimal("500")
        assert m4["expense"] == Decimal("200")
        assert m4["net"] == Decimal("300")

    async def test_transfers_excluded_from_monthly_totals(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, TRANSFER_TX]

        result = await service.get_monthly_trend(year=2026)

        assert len(result["months"]) == 1
        m4 = result["months"][0]
        assert m4["income"] == Decimal("500")
        assert m4["expense"] == Decimal("0")

    async def test_refunds_excluded_from_monthly_totals(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [
            EXPENSE_TX,
            REFUND_TX,
        ]

        result = await service.get_monthly_trend(year=2026)

        # month 4 has expense, month 3 has refund (excluded) — only month 4
        months_by_m = {m["month"]: m for m in result["months"]}
        assert 4 in months_by_m
        assert months_by_m[4]["expense"] == Decimal("200")
        assert 3 not in months_by_m  # refund excluded entirely

    async def test_only_transfers_produces_empty(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [TRANSFER_TX]

        result = await service.get_monthly_trend(year=2026)

        assert result["months"] == []


# ---------------------------------------------------------------------------
# GET /by-account — transactionType classification + count includes all
# ---------------------------------------------------------------------------


class TestGetByAccount:
    async def test_income_expense_by_account(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, EXPENSE_TX]

        result = await service.get_by_account(year=2026)

        items = {item["account_id"]: item for item in result["items"]}
        assert items["acc-001"]["total_income"] == Decimal("500")
        assert items["acc-001"]["total_expense"] == Decimal("200")
        assert items["acc-001"]["transaction_count"] == 2

    async def test_transfers_excluded_from_totals_but_counted(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX, TRANSFER_TX]

        result = await service.get_by_account(year=2026)

        items = {item["account_id"]: item for item in result["items"]}
        acc = items["acc-001"]
        assert acc["total_income"] == Decimal("500")
        assert acc["total_expense"] == Decimal("0")
        assert acc["transaction_count"] == 2  # transfer counted

    async def test_refunds_excluded_from_totals_but_counted(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [EXPENSE_TX, REFUND_TX]

        result = await service.get_by_account(year=2026)

        items = {item["account_id"]: item for item in result["items"]}
        assert items["acc-001"]["total_expense"] == Decimal("200")
        assert items["acc-001"]["transaction_count"] == 1
        assert items["acc-002"]["total_income"] == Decimal("0")
        assert items["acc-002"]["total_expense"] == Decimal("0")
        assert items["acc-002"]["transaction_count"] == 1  # refund counted

    async def test_all_types_counts_everything(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = ALL_TYPES

        result = await service.get_by_account(year=2026)

        items = {item["account_id"]: item for item in result["items"]}
        # acc-001: income(500) + expense(200) + transfer + uncategorized_income(75) = 4 txns
        assert items["acc-001"]["transaction_count"] == 4
        assert items["acc-001"]["total_income"] == Decimal("575")
        assert items["acc-001"]["total_expense"] == Decimal("200")
        # acc-002: refund only = 1 txn, 0 income/expense
        assert items["acc-002"]["transaction_count"] == 1
        assert items["acc-002"]["total_income"] == Decimal("0")
        assert items["acc-002"]["total_expense"] == Decimal("0")


# ---------------------------------------------------------------------------
# GET /balance â€” category + subcategory grouping
# ---------------------------------------------------------------------------


class TestGetBalance:
    async def test_groups_by_category_and_subcategory(self, service, mock_txn_svc):
        mock_txn_svc.get_transactions_for_report.return_value = [
            {
                "categoryId": "cat-donations",
                "subcategoryId": "subcat-individual",
                "accountId": "acc-001",
                "amount": 500.0,
                "month": 4,
                "transactionType": "income",
            },
            {
                "categoryId": "cat-supplies",
                "subcategoryId": None,
                "accountId": "acc-001",
                "amount": -200.0,
                "month": 4,
                "transactionType": "expense",
            },
        ]

        result = await service.get_balance(year=2026)

        items = {(item["category_id"], item["subcategory_id"]): item for item in result["items"]}
        assert items[("cat-donations", "subcat-individual")]["category_name"] == "Donations"
        assert items[("cat-donations", "subcat-individual")]["subcategory_name"] == "Individual"
        assert items[("cat-donations", "subcat-individual")]["income"] == Decimal("500")
        assert items[("cat-supplies", None)]["category_name"] == "Supplies"
        assert items[("cat-supplies", None)]["expense"] == Decimal("200")

    async def test_balance_empty_year(self, service, mock_txn_svc):
        """Balance for a year with no transactions returns empty items list."""
        mock_txn_svc.get_transactions_for_report.return_value = []

        result = await service.get_balance(year=2025)

        assert result["year"] == 2025
        assert result["items"] == []

    async def test_balance_includes_subcategory_from_fixtures(self, service, mock_txn_svc):
        """Transactions with subcategoryId are grouped and named correctly."""
        mock_txn_svc.get_transactions_for_report.return_value = [INCOME_TX]

        result = await service.get_balance(year=2026)

        assert len(result["items"]) == 1
        item = result["items"][0]
        assert item["category_id"] == "cat-donations"
        assert item["subcategory_id"] == "subcat-individual"
        assert item["subcategory_name"] == "Individual"
        assert item["income"] == Decimal("500")
        assert item["expense"] == Decimal("0")
        assert item["net"] == Decimal("500")


# ---------------------------------------------------------------------------
# Split-aware report tests — by_category uses split lines when isSplit=True
# ---------------------------------------------------------------------------

SPLIT_EXPENSE_TX = {
    "categoryId": None,  # parent category cleared after split
    "accountId": "acc-001",
    "amount": -150.0,
    "month": 4,
    "transactionType": "expense",
    "isSplit": True,
    "splitLines": [
        {"amount": -100.0, "categoryId": "cat-rent", "subcategoryId": None, "tagIds": []},
        {"amount": -50.0, "categoryId": "cat-supplies", "subcategoryId": None, "tagIds": []},
    ],
}

SPLIT_INCOME_TX = {
    "categoryId": None,
    "accountId": "acc-001",
    "amount": 1200.0,
    "month": 4,
    "transactionType": "income",
    "isSplit": True,
    "splitLines": [
        {"amount": 500.0, "categoryId": "cat-grants", "subcategoryId": None, "tagIds": []},
        {"amount": 400.0, "categoryId": "cat-donations", "subcategoryId": None, "tagIds": []},
        {"amount": 300.0, "categoryId": None, "subcategoryId": None, "tagIds": []},
    ],
}


class TestSplitAwareByCategory:
    async def test_split_expense_uses_line_categories(self, service, mock_txn_svc):
        """Split parent category (null) should be ignored; lines' categories are used."""
        mock_txn_svc.get_transactions_for_report.return_value = [SPLIT_EXPENSE_TX]

        result = await service.get_by_category(year=2026)
        items = {item["category_id"]: item for item in result["items"]}

        assert "cat-rent" in items
        assert items["cat-rent"]["expense"] == Decimal("100")
        assert "cat-supplies" in items
        assert items["cat-supplies"]["expense"] == Decimal("50")
        # Parent's null categoryId should NOT appear as "uncategorized"
        assert "uncategorized" not in items

    async def test_split_income_uses_line_categories(self, service, mock_txn_svc):
        """Split income lines are aggregated by their own categories."""
        mock_txn_svc.get_transactions_for_report.return_value = [SPLIT_INCOME_TX]

        result = await service.get_by_category(year=2026)
        items = {item["category_id"]: item for item in result["items"]}

        assert items["cat-grants"]["income"] == Decimal("500")
        assert items["cat-donations"]["income"] == Decimal("400")
        # Third line has no category — goes to uncategorized
        assert items["uncategorized"]["income"] == Decimal("300")

    async def test_mixed_split_and_regular_transactions(self, service, mock_txn_svc):
        """Split and non-split transactions aggregate correctly together."""
        mock_txn_svc.get_transactions_for_report.return_value = [
            INCOME_TX,  # cat-donations, 500 income
            SPLIT_EXPENSE_TX,  # split: cat-rent(-100) + cat-supplies(-50)
        ]

        result = await service.get_by_category(year=2026)
        items = {item["category_id"]: item for item in result["items"]}

        # Regular income tx
        assert items["cat-donations"]["income"] == Decimal("500")
        # Split expense lines
        assert items["cat-rent"]["expense"] == Decimal("100")
        assert items["cat-supplies"]["expense"] == Decimal("50")

    async def test_split_transaction_in_summary_uses_parent_amount(self, service, mock_txn_svc):
        """Summary totals use parent amount (no double counting from split lines)."""
        mock_txn_svc.get_transactions_for_report.return_value = [SPLIT_EXPENSE_TX]

        result = await service.get_summary(year=2026)

        assert result["total_expense"] == Decimal("150")
        assert result["total_income"] == Decimal("0")

    async def test_split_transaction_in_monthly_trend(self, service, mock_txn_svc):
        """Monthly trend uses parent amount, not split line amounts."""
        mock_txn_svc.get_transactions_for_report.return_value = [SPLIT_EXPENSE_TX]

        result = await service.get_monthly_trend(year=2026)

        assert len(result["months"]) == 1
        assert result["months"][0]["expense"] == Decimal("150")

    async def test_split_transaction_in_by_account(self, service, mock_txn_svc):
        """By-account report uses parent amount and counts split as one transaction."""
        mock_txn_svc.get_transactions_for_report.return_value = [SPLIT_EXPENSE_TX]

        result = await service.get_by_account(year=2026)
        items = {item["account_id"]: item for item in result["items"]}

        assert items["acc-001"]["transaction_count"] == 1
        assert items["acc-001"]["total_expense"] == Decimal("150")
