"""Tests for TransactionService — business logic with mocked repository."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.domain import AuditAction, ReviewStatus, TransactionType
from app.models.schemas import SplitLineCreate, TransactionCreate, TransactionUpdate
from app.services.transaction_service import TransactionService

from .conftest import make_transaction

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.aggregate_filtered.return_value = {
        "total_income": Decimal("0"),
        "total_expenses": Decimal("0"),
        "net": Decimal("0"),
        "transaction_count": 0,
        "uncategorized_count": 0,
    }
    return repo


@pytest.fixture
def mock_audit():
    return AsyncMock()


@pytest.fixture
def mock_category_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = {
        "id": "cat-001",
        "categoryType": "income",
        "name": "Default Category",
        "isActive": True,
        "subcategories": [
            {"id": "subcat-001", "name": "Sub 1", "isActive": True},
            {"id": "subcat-002", "name": "Sub 2", "isActive": True},
        ],
    }
    return repo


@pytest.fixture
def service(mock_repo, mock_audit, mock_category_repo):
    return TransactionService(repo=mock_repo, audit_service=mock_audit, category_repo=mock_category_repo)


USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"


# ---------------------------------------------------------------------------
# list_transactions
# ---------------------------------------------------------------------------


class TestListTransactions:
    async def test_builds_correct_partition_key(self, service, mock_repo):
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(year=2026, month=4)

        mock_repo.list_by_partition.assert_awaited_once_with(
            "2026-04",
            filters=None,
            include_deleted=False,
            page_size=50,
            continuation_token=None,
        )

    async def test_zero_pads_single_digit_month(self, service, mock_repo):
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(year=2026, month=1)

        mock_repo.list_by_partition.assert_awaited_once_with(
            "2026-01",
            filters=None,
            include_deleted=False,
            page_size=50,
            continuation_token=None,
        )

    async def test_passes_filters(self, service, mock_repo):
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(
            year=2026,
            month=4,
            account_id="acc-001",
            category_id="cat-001",
            subcategory_id="subcat-001",
            tag_id="tag-001",
            search="donation",
            amount_min=Decimal("10.00"),
            amount_max=Decimal("500.00"),
            include_deleted=True,
            page_size=25,
            continuation_token="tok123",
        )

        mock_repo.list_by_partition.assert_awaited_once_with(
            "2026-04",
            filters={
                "accountId": "acc-001",
                "categoryId": "cat-001",
                "subcategoryId": "subcat-001",
                "tagId": "tag-001",
                "search": "donation",
                "amountMin": 10.00,
                "amountMax": 500.00,
            },
            include_deleted=True,
            page_size=25,
            continuation_token="tok123",
        )

    async def test_returns_items_and_token(self, service, mock_repo):
        items = [make_transaction(), make_transaction()]
        mock_repo.list_by_partition.return_value = (items, "next-tok")

        result_items, token, aggregates = await service.list_transactions(year=2026, month=4)

        assert result_items == items
        assert token == "next-tok"
        assert aggregates is not None

    async def test_first_page_returns_aggregates(self, service, mock_repo):
        mock_repo.list_by_partition.return_value = ([], None)
        mock_repo.aggregate_filtered.return_value = {
            "total_income": Decimal("500.00"),
            "total_expenses": Decimal("200.00"),
            "net": Decimal("300.00"),
            "transaction_count": 10,
            "uncategorized_count": 2,
        }

        _, _, aggregates = await service.list_transactions(year=2026, month=4)

        assert aggregates["total_income"] == Decimal("500.00")
        assert aggregates["total_expenses"] == Decimal("200.00")
        assert aggregates["net"] == Decimal("300.00")
        assert aggregates["transaction_count"] == 10
        assert aggregates["uncategorized_count"] == 2

    async def test_subsequent_page_returns_none_aggregates(self, service, mock_repo):
        mock_repo.list_by_partition.return_value = ([], None)

        _, _, aggregates = await service.list_transactions(year=2026, month=4, continuation_token="page2")

        assert aggregates is None
        mock_repo.aggregate_filtered.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_transaction
# ---------------------------------------------------------------------------


class TestGetTransaction:
    async def test_returns_item(self, service, mock_repo):
        tx = make_transaction()
        mock_repo.get_by_id.return_value = tx

        result = await service.get_transaction("tx-001", year=2026, month=4)

        assert result == tx
        mock_repo.get_by_id.assert_awaited_once_with("tx-001", "2026-04")

    async def test_returns_none_for_deleted(self, service, mock_repo):
        tx = make_transaction(isDeleted=True)
        mock_repo.get_by_id.return_value = tx

        result = await service.get_transaction("tx-001", year=2026, month=4)

        assert result is None

    async def test_returns_none_when_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None

        result = await service.get_transaction("tx-nonexistent", year=2026, month=4)

        assert result is None


# ---------------------------------------------------------------------------
# create_transaction
# ---------------------------------------------------------------------------


class TestCreateTransaction:
    async def test_builds_document(self, service, mock_repo, mock_audit):
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("150.50"),
            currency="EUR",
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-001",
            subcategory_id="subcat-001",
            tag_ids=["tag-001"],
            detail="Monthly donation",
        )
        mock_repo.create.return_value = {"id": "tx-new", "amount": 150.50}

        result = await service.create_transaction(data, USER_ID, USER_NAME)

        assert result == {"id": "tx-new", "amount": 150.50}

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["type"] == "transaction"
        assert call_args["partitionKey"] == "2026-04"
        assert call_args["date"] == "2026-04-10"
        assert call_args["year"] == 2026
        assert call_args["month"] == 4
        assert call_args["amount"] == 150.50
        assert call_args["currency"] == "EUR"
        assert call_args["accountId"] == "acc-001"
        assert call_args["categoryId"] == "cat-001"
        assert call_args["subcategoryId"] == "subcat-001"
        assert call_args["tagIds"] == ["tag-001"]
        assert call_args["detail"] == "Monthly donation"
        assert call_args["createdBy"] == USER_ID
        assert call_args["createdByName"] == USER_NAME
        assert call_args["isDeleted"] is False
        assert call_args["updatedBy"] is None
        assert call_args["transactionType"] == "income"
        assert call_args["categorizationStatus"] == "manually_categorized"
        assert call_args["reviewStatus"] == "approved"
        assert call_args["notes"] == []
        assert call_args["originalAmount"] is None
        assert call_args["originalDate"] is None

    async def test_value_date_defaults_to_date(self, service, mock_repo, mock_audit):
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("50.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-001",
            subcategory_id="subcat-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["valueDate"] == "2026-04-10"

    async def test_calls_audit(self, service, mock_repo, mock_audit):
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("150.50"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-001",
            subcategory_id="subcat-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        mock_audit.log.assert_awaited_once_with(
            entity_type="Transaction",
            entity_id="tx-new",
            action=AuditAction.CREATE,
            changed_by=USER_ID,
            changed_by_name=USER_NAME,
            new_values={
                "amount": 150.50,
                "transactionType": "income",
                "accountId": "acc-001",
                "categoryId": "cat-001",
            },
        )


# ---------------------------------------------------------------------------
# update_transaction
# ---------------------------------------------------------------------------


class TestUpdateTransaction:
    async def test_tracks_changes(self, service, mock_repo, mock_audit):
        existing = make_transaction(
            id="tx-001",
            amount=100.0,
            categoryId="cat-001",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "amount": 200.0, "categoryId": "cat-002"}

        data = TransactionUpdate(amount=Decimal("200.00"), category_id="cat-002")

        result = await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        assert result is not None
        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["action"] == AuditAction.UPDATE
        assert audit_call.kwargs["entity_id"] == "tx-001"

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        data = TransactionUpdate(amount=Decimal("200.00"))

        result = await service.update_transaction("tx-missing", 2026, 4, data, USER_ID, USER_NAME)

        assert result is None
        mock_repo.replace.assert_not_awaited()
        mock_audit.log.assert_not_awaited()

    async def test_no_audit_when_no_changes(self, service, mock_repo, mock_audit):
        """If the update payload matches existing values, no audit entry should be created."""
        existing = make_transaction(id="tx-001", amount=150.50, categoryId="cat-001", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        # Same categoryId — no actual change via model_dump(exclude_unset, by_alias)
        data = TransactionUpdate(category_id="cat-001")

        await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        mock_audit.log.assert_not_awaited()


# ---------------------------------------------------------------------------
# soft_delete_transaction
# ---------------------------------------------------------------------------


class TestSoftDelete:
    async def test_sets_flag(self, service, mock_repo, mock_audit):
        existing = make_transaction(id="tx-001", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "isDeleted": True}

        result = await service.soft_delete_transaction("tx-001", 2026, 4, USER_ID, USER_NAME)

        assert result is True
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["isDeleted"] is True
        assert replace_arg["updatedBy"] == USER_ID

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["action"] == AuditAction.DELETE
        assert audit_call.kwargs["old_values"] == {"isDeleted": False}
        assert audit_call.kwargs["new_values"] == {"isDeleted": True}

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        result = await service.soft_delete_transaction("tx-missing", 2026, 4, USER_ID, USER_NAME)

        assert result is False
        mock_repo.replace.assert_not_awaited()
        mock_audit.log.assert_not_awaited()


# ---------------------------------------------------------------------------
# Delegation pass-throughs
# ---------------------------------------------------------------------------


class TestDelegation:
    async def test_count_by_account_delegates(self, service, mock_repo):
        mock_repo.count_by_account.return_value = 42

        result = await service.count_by_account("acc-001")

        assert result == 42
        mock_repo.count_by_account.assert_awaited_once_with("acc-001")

    async def test_get_transactions_for_report_delegates(self, service, mock_repo):
        mock_repo.query_for_report.return_value = [{"amount": 100}]

        result = await service.get_transactions_for_report(year=2026, month=4, account_id="acc-001")

        assert result == [{"amount": 100}]
        mock_repo.query_for_report.assert_awaited_once_with(2026, 4, "acc-001")

    async def test_count_by_category_delegates(self, service, mock_repo):
        mock_repo.count_by_category.return_value = 5

        result = await service.count_by_category("cat-001")

        assert result == 5
        mock_repo.count_by_category.assert_awaited_once_with("cat-001")

    async def test_count_by_tag_delegates(self, service, mock_repo):
        mock_repo.count_by_tag.return_value = 3

        result = await service.count_by_tag("tag-001")

        assert result == 3
        mock_repo.count_by_tag.assert_awaited_once_with("tag-001")


# ---------------------------------------------------------------------------
# Auto-sign amount based on category type
# ---------------------------------------------------------------------------


class TestAutoSignAmount:
    """Tests for automatic amount signing based on transactionType (v2)."""

    async def test_create_income_positive(self, service, mock_repo, mock_audit, mock_category_repo):
        """income transactionType → amount stored as positive."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-inc",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [{"id": "subcat-001", "name": "Sub", "isActive": True}],
        }
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-inc",
            subcategory_id="subcat-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["amount"] == 100.00

    async def test_create_expense_negative(self, service, mock_repo, mock_audit, mock_category_repo):
        """expense transactionType → amount stored as negative."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-exp",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [{"id": "subcat-001", "name": "Sub", "isActive": True}],
        }
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.EXPENSE,
            category_id="cat-exp",
            subcategory_id="subcat-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["amount"] == -100.00

    async def test_create_transfer_preserves_sign(self, service, mock_repo, mock_audit, mock_category_repo):
        """transfer → amount as-entered (AS-003)."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("-500.00"),
            account_id="acc-001",
            transaction_type=TransactionType.TRANSFER,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["amount"] == -500.00

    async def test_create_refund_preserves_sign(self, service, mock_repo, mock_audit, mock_category_repo):
        """refund → amount as-entered (AS-004)."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("200.00"),
            account_id="acc-001",
            transaction_type=TransactionType.REFUND,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["amount"] == 200.00

    async def test_create_uncategorized_sets_status(self, service, mock_repo, mock_audit, mock_category_repo):
        """No category → categorizationStatus = uncategorized (CS-001)."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["categorizationStatus"] == "uncategorized"
        assert call_args["categoryId"] is None
        assert call_args["subcategoryId"] is None

    async def test_create_categorized_sets_status(self, service, mock_repo, mock_audit, mock_category_repo):
        """With category → categorizationStatus = manually_categorized (CS-002)."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["categorizationStatus"] == "manually_categorized"

    async def test_create_review_status_defaults_approved(self, service, mock_repo, mock_audit, mock_category_repo):
        """Manual creation defaults to reviewStatus = approved (RS-001)."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["reviewStatus"] == "approved"

    async def test_create_allows_mismatched_category_type(self, service, mock_repo, mock_audit, mock_category_repo):
        """income transaction + expense category is allowed — categoryType is guidance only."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-exp",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [],
        }
        mock_repo.create.return_value = {"id": "tx-new"}
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-exp",
        )

        result = await service.create_transaction(data, USER_ID, USER_NAME)
        assert result["id"] == "tx-new"

    async def test_update_type_change_resigns(self, service, mock_repo, mock_audit, mock_category_repo):
        """Changing transactionType from income to expense re-signs amount (AS-005)."""
        existing = make_transaction(
            id="tx-001",
            amount=100.0,
            transactionType="income",
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "amount": -100.0, "transactionType": "expense"}

        data = TransactionUpdate(transaction_type=TransactionType.EXPENSE)

        result = await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["amount"] == -100.0
        assert replace_arg["transactionType"] == "expense"

    async def test_update_category_change_does_not_resign(self, service, mock_repo, mock_audit, mock_category_repo):
        """Category changes do NOT trigger re-signing (AS-007)."""
        existing = make_transaction(
            id="tx-001",
            amount=100.0,
            transactionType="income",
            categoryId="cat-inc-1",
            subcategoryId=None,
            categorizationStatus="manually_categorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "categoryId": "cat-001"}

        mock_category_repo.get_by_id.return_value = {
            "id": "cat-001",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [],
        }

        data = TransactionUpdate(category_id="cat-001")

        result = await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        # Amount stays 100.0 — category changes don't re-sign
        assert replace_arg["amount"] == 100.0

    async def test_update_amount_resigns_based_on_current_type(
        self, service, mock_repo, mock_audit, mock_category_repo
    ):
        """Change amount without changing type → re-signed based on current transactionType (AS-006)."""
        existing = make_transaction(
            id="tx-001",
            amount=-50.0,
            transactionType="expense",
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "amount": -200.0}

        data = TransactionUpdate(amount=Decimal("200.00"))

        result = await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["amount"] == -200.0

    async def test_update_correction_preservation_amount(self, service, mock_repo, mock_audit, mock_category_repo):
        """First edit of amount saves originalAmount (TC-001)."""
        existing = make_transaction(
            id="tx-001",
            amount=100.0,
            transactionType="income",
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            originalAmount=None,
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "amount": 200.0}

        data = TransactionUpdate(amount=Decimal("200.00"))
        await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["originalAmount"] == 100.0

    async def test_update_correction_preservation_write_once(self, service, mock_repo, mock_audit, mock_category_repo):
        """originalAmount is write-once — never overwritten (TC-003)."""
        existing = make_transaction(
            id="tx-001",
            amount=200.0,
            transactionType="income",
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            originalAmount=50.0,
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "amount": 300.0}

        data = TransactionUpdate(amount=Decimal("300.00"))
        await service.update_transaction("tx-001", 2026, 4, data, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["originalAmount"] == 50.0  # kept original, not overwritten


# ---------------------------------------------------------------------------
# FR-009: Source reference
# ---------------------------------------------------------------------------


class TestSourceReference:
    """FR-009: sourceReference field tests."""

    async def test_create_with_source_reference(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-009.1: sourceReference stored when provided."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            source_reference="REF-2026-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["sourceReference"] == "REF-2026-001"

    async def test_create_without_source_reference_defaults_none(
        self, service, mock_repo, mock_audit, mock_category_repo
    ):
        """AC-009.2: sourceReference defaults to null."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["sourceReference"] is None


# ---------------------------------------------------------------------------
# FR-011: Counterparty information
# ---------------------------------------------------------------------------


class TestCounterparty:
    """FR-011: Counterparty information tests."""

    async def test_create_with_counterparty(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-011.1: counterparty fields stored."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            counterparty_name="Fundación X",
            counterparty_reference="CP-001",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["counterpartyName"] == "Fundación X"
        assert call_args["counterpartyReference"] == "CP-001"

    async def test_create_without_counterparty_defaults_none(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-011.2: counterparty fields default to null."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        await service.create_transaction(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["counterpartyName"] is None
        assert call_args["counterpartyReference"] is None


# ---------------------------------------------------------------------------
# FR-012: Corrections (originalDate)
# ---------------------------------------------------------------------------


class TestCorrections:
    """FR-012: Correction preservation tests."""

    async def test_original_date_preserved_on_first_edit(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-012.3: originalDate preserved on first date edit."""
        existing = make_transaction(
            id="tx-001",
            amount=100.0,
            transactionType="income",
            date="2026-03-15",
            originalDate=None,
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "date": "2026-03-16"}

        data = TransactionUpdate(transaction_date=date(2026, 3, 16))
        await service.update_transaction("tx-001", 2026, 3, data, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["originalDate"] == "2026-03-15"
        assert replace_arg["date"] == "2026-03-16"


# ---------------------------------------------------------------------------
# FR-016/018: Validation (subcategory rules)
# ---------------------------------------------------------------------------


class TestValidation:
    """FR-016.3, FR-018, FR-010.8: Validation tests."""

    async def test_subcategory_without_category_raises(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-016.3: subcategoryId without categoryId → ValueError."""
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id=None,
            subcategory_id="subcat-001",
        )

        with pytest.raises(ValueError, match="subcategoryId can only be set when categoryId is also set"):
            await service.create_transaction(data, USER_ID, USER_NAME)

    async def test_subcategory_not_in_category_raises(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-018.1: subcategory must belong to category."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-A",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [
                {"id": "sub1", "name": "Sub 1", "isActive": True},
                {"id": "sub2", "name": "Sub 2", "isActive": True},
            ],
        }
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-A",
            subcategory_id="sub3",
        )

        with pytest.raises(ValueError, match="does not belong to category"):
            await service.create_transaction(data, USER_ID, USER_NAME)

    async def test_inactive_subcategory_rejected(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-018.2: inactive subcategory → ValueError."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-A",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [
                {"id": "sub1", "name": "Sub 1", "isActive": False},
            ],
        }
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("100.00"),
            account_id="acc-001",
            transaction_type=TransactionType.INCOME,
            category_id="cat-A",
            subcategory_id="sub1",
        )

        with pytest.raises(ValueError, match="does not belong to category.*or is inactive"):
            await service.create_transaction(data, USER_ID, USER_NAME)

    async def test_transfer_allows_any_category_type(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-010.8: transfer + expense category is allowed (no cross-validation)."""
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-exp",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [],
        }
        data = TransactionCreate(
            date=date(2026, 4, 10),
            amount=Decimal("-500.00"),
            account_id="acc-001",
            transaction_type=TransactionType.TRANSFER,
            category_id="cat-exp",
        )
        mock_repo.create.return_value = {"id": "tx-new"}

        result = await service.create_transaction(data, USER_ID, USER_NAME)

        assert result["id"] == "tx-new"


# ---------------------------------------------------------------------------
# FR-017/021: Categorize transaction
# ---------------------------------------------------------------------------


class TestCategorizeTransaction:
    """FR-017: Re-categorize and FR-021: categorization status tests."""

    async def test_categorize_sets_manually_categorized(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-021.2: assigning a category via categorize → manually_categorized."""
        existing = make_transaction(
            id="tx-001",
            categoryId=None,
            subcategoryId=None,
            categorizationStatus="uncategorized",
            transactionType="income",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {
            **existing,
            "categoryId": "cat-001",
            "categorizationStatus": "manually_categorized",
        }
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-001",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [],
        }

        result = await service.categorize_transaction("tx-001", 2026, 4, "cat-001", None, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["categoryId"] == "cat-001"
        assert replace_arg["categorizationStatus"] == "manually_categorized"

    async def test_remove_category_sets_uncategorized(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-017.2: remove category → uncategorized."""
        existing = make_transaction(
            id="tx-001",
            categoryId="cat-001",
            subcategoryId="subcat-001",
            categorizationStatus="manually_categorized",
            transactionType="income",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {
            **existing,
            "categoryId": None,
            "subcategoryId": None,
            "categorizationStatus": "uncategorized",
        }

        result = await service.categorize_transaction("tx-001", 2026, 4, None, None, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["categoryId"] is None
        assert replace_arg["subcategoryId"] is None
        assert replace_arg["categorizationStatus"] == "uncategorized"

    async def test_recategorize_allows_mismatched_type(self, service, mock_repo, mock_audit, mock_category_repo):
        """expense transaction + income category is allowed — categoryType is guidance only."""
        existing = make_transaction(
            id="tx-001",
            categoryId="cat-exp",
            transactionType="expense",
            categorizationStatus="manually_categorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-inc",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [],
        }
        mock_repo.replace.return_value = {**existing, "categoryId": "cat-inc"}

        result = await service.categorize_transaction("tx-001", 2026, 4, "cat-inc", None, USER_ID, USER_NAME)
        assert result["categoryId"] == "cat-inc"


# ---------------------------------------------------------------------------
# FR-030-034: Review workflow
# ---------------------------------------------------------------------------


class TestReviewTransaction:
    """FR-030–034: Review workflow tests."""

    async def test_review_sets_status_and_reviewer(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-031.1: review sets status and reviewer info."""
        existing = make_transaction(
            id="tx-001",
            reviewStatus="pending",
            reviewedBy=None,
            reviewedByName=None,
            reviewedAt=None,
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {
            **existing,
            "reviewStatus": "approved",
            "reviewedBy": USER_ID,
            "reviewedByName": USER_NAME,
        }

        result = await service.review_transaction("tx-001", 2026, 4, ReviewStatus.APPROVED, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["reviewStatus"] == "approved"
        assert replace_arg["reviewedBy"] == USER_ID
        assert replace_arg["reviewedByName"] == USER_NAME
        assert replace_arg["reviewedAt"] is not None

    async def test_review_flagged(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-032.1: flag for follow-up."""
        existing = make_transaction(id="tx-001", reviewStatus="approved", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "reviewStatus": "flagged"}

        result = await service.review_transaction("tx-001", 2026, 4, ReviewStatus.FLAGGED, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["reviewStatus"] == "flagged"

    async def test_review_tracks_identity_and_audit(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-034.1: reviewer identity tracked in doc and audit log."""
        existing = make_transaction(id="tx-001", reviewStatus="pending", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "reviewStatus": "reviewed"}

        await service.review_transaction("tx-001", 2026, 4, ReviewStatus.REVIEWED, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["reviewedBy"] == USER_ID
        assert replace_arg["reviewedByName"] == USER_NAME
        assert replace_arg["reviewedAt"] is not None

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["old_values"] == {"reviewStatus": "pending"}
        assert audit_call.kwargs["new_values"] == {"reviewStatus": "reviewed"}


# ---------------------------------------------------------------------------
# FR-033: Notes
# ---------------------------------------------------------------------------


class TestAddNote:
    """FR-033: Notes tests."""

    async def test_add_note_creates_note_with_fields(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-033.1: note appended with id, text, author, authorName, createdAt."""
        existing = make_transaction(id="tx-001", notes=[], isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        result = await service.add_note("tx-001", 2026, 4, "Test note", USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        notes = replace_arg["notes"]
        assert len(notes) == 1
        note = notes[0]
        assert note["text"] == "Test note"
        assert note["author"] == USER_ID
        assert note["authorName"] == USER_NAME
        assert "id" in note
        assert "createdAt" in note

    async def test_add_note_preserves_existing_notes(self, service, mock_repo, mock_audit, mock_category_repo):
        """AC-033.2: notes are append-only — existing notes preserved."""
        existing_note = {
            "id": "note-old",
            "text": "Old note",
            "author": "other-user",
            "authorName": "Other User",
            "createdAt": "2026-04-01T10:00:00Z",
        }
        existing = make_transaction(id="tx-001", notes=[existing_note], isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        await service.add_note("tx-001", 2026, 4, "New note", USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        notes = replace_arg["notes"]
        assert len(notes) == 2
        assert notes[0]["id"] == "note-old"
        assert notes[0]["text"] == "Old note"
        assert notes[1]["text"] == "New note"


# ---------------------------------------------------------------------------
# List transaction filters (new v2 filters)
# ---------------------------------------------------------------------------


class TestListTransactionFilters:
    """FR-021.3, FR-034.2: New v2 filter parameter tests."""

    async def test_passes_categorization_status_filter(self, service, mock_repo):
        """AC-021.3: filter by categorizationStatus."""
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(year=2026, month=4, categorization_status="uncategorized")

        filters = mock_repo.list_by_partition.call_args.kwargs["filters"]
        assert filters["categorizationStatus"] == "uncategorized"

    async def test_passes_review_status_filter(self, service, mock_repo):
        """AC-034.2: filter by reviewStatus."""
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(year=2026, month=4, review_status="pending")

        filters = mock_repo.list_by_partition.call_args.kwargs["filters"]
        assert filters["reviewStatus"] == "pending"

    async def test_passes_transaction_type_filter(self, service, mock_repo):
        """Filter by transactionType."""
        mock_repo.list_by_partition.return_value = ([], None)

        await service.list_transactions(year=2026, month=4, transaction_type="income")

        filters = mock_repo.list_by_partition.call_args.kwargs["filters"]
        assert filters["transactionType"] == "income"


# ---------------------------------------------------------------------------
# split_transaction
# ---------------------------------------------------------------------------


class TestSplitTransaction:
    """Tests for the split transaction feature."""

    async def test_split_stores_split_lines(self, service, mock_repo, mock_audit, mock_category_repo):
        """Splitting stores lines in the parent transaction document."""
        existing = make_transaction(id="tx-001", amount=-150.00, transactionType="expense", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        splits = [
            SplitLineCreate(amount=Decimal("100.00"), category_id="cat-001"),
            SplitLineCreate(amount=Decimal("50.00"), category_id="cat-001"),
        ]
        # Make category validation pass
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-001",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [],
        }

        result = await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        assert result is not None
        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["isSplit"] is True
        assert len(replace_arg["splits"]) == 2
        assert replace_arg["splits"][0]["amount"] == 100.00
        assert replace_arg["splits"][1]["amount"] == 50.00

    async def test_split_sets_is_split_flag(self, service, mock_repo, mock_audit, mock_category_repo):
        """Splitting marks isSplit = True on parent."""
        existing = make_transaction(id="tx-001", amount=200.00, transactionType="income", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-001",
            "categoryType": "income",
            "isActive": True,
            "subcategories": [],
        }

        splits = [
            SplitLineCreate(amount=Decimal("120.00"), category_id="cat-001"),
            SplitLineCreate(amount=Decimal("80.00"), category_id="cat-001"),
        ]

        await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert replace_arg["isSplit"] is True

    async def test_split_raises_when_totals_mismatch(self, service, mock_repo, mock_audit, mock_category_repo):
        """ValueError raised when split totals do not match parent amount."""
        existing = make_transaction(id="tx-001", amount=-150.00, transactionType="expense", isDeleted=False)
        mock_repo.get_by_id.return_value = existing

        splits = [
            SplitLineCreate(amount=Decimal("100.00")),
            SplitLineCreate(amount=Decimal("40.00")),  # total = 140, not 150
        ]

        with pytest.raises(ValueError, match="must equal"):
            await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

    async def test_split_returns_none_for_missing_transaction(self, service, mock_repo, mock_audit, mock_category_repo):
        """Returns None when transaction does not exist."""
        mock_repo.get_by_id.return_value = None

        splits = [
            SplitLineCreate(amount=Decimal("50.00")),
            SplitLineCreate(amount=Decimal("50.00")),
        ]

        result = await service.split_transaction("tx-missing", 2026, 4, splits, USER_ID, USER_NAME)

        assert result is None

    async def test_split_logs_audit_entry(self, service, mock_repo, mock_audit, mock_category_repo):
        """Splitting creates an audit log entry."""
        existing = make_transaction(id="tx-001", amount=-100.00, transactionType="expense", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        splits = [
            SplitLineCreate(amount=Decimal("60.00")),
            SplitLineCreate(amount=Decimal("40.00")),
        ]

        await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args.kwargs
        assert audit_call["entity_type"] == "Transaction"
        assert audit_call["entity_id"] == "tx-001"
        assert audit_call["action"] == AuditAction.UPDATE
        assert audit_call["new_values"]["splits_count"] == 2

    async def test_split_each_line_has_id(self, service, mock_repo, mock_audit, mock_category_repo):
        """Each split line gets a generated UUID id."""
        existing = make_transaction(id="tx-001", amount=-50.00, transactionType="expense", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        splits = [
            SplitLineCreate(amount=Decimal("30.00")),
            SplitLineCreate(amount=Decimal("20.00")),
        ]

        await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        lines = replace_arg["splits"]
        for line in lines:
            assert "id" in line
            assert len(line["id"]) > 0

    async def test_split_stores_category_and_tags_per_line(self, service, mock_repo, mock_audit, mock_category_repo):
        """Each split line preserves its category, subcategory, tags, and detail."""
        existing = make_transaction(id="tx-001", amount=-100.00, transactionType="expense", isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing
        mock_category_repo.get_by_id.return_value = {
            "id": "cat-001",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [{"id": "subcat-001", "name": "Sub 1", "isActive": True}],
        }

        splits = [
            SplitLineCreate(
                amount=Decimal("60.00"),
                category_id="cat-001",
                subcategory_id="subcat-001",
                tag_ids=["tag-001"],
                detail="Printing",
            ),
            SplitLineCreate(
                amount=Decimal("40.00"),
                category_id="cat-001",
                detail="Merchandise",
            ),
        ]

        await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        lines = replace_arg["splits"]
        assert lines[0]["categoryId"] == "cat-001"
        assert lines[0]["subcategoryId"] == "subcat-001"
        assert lines[0]["tagIds"] == ["tag-001"]
        assert lines[0]["detail"] == "Printing"
        assert lines[1]["detail"] == "Merchandise"

    async def test_replace_existing_splits(self, service, mock_repo, mock_audit, mock_category_repo):
        """Re-splitting replaces previous split lines."""
        old_split = {"id": "split-old", "amount": 75.00, "categoryId": None, "subcategoryId": None, "tagIds": [], "detail": None}
        existing = make_transaction(id="tx-001", amount=-150.00, transactionType="expense", isSplit=True, splits=[old_split], isDeleted=False)
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        splits = [
            SplitLineCreate(amount=Decimal("100.00")),
            SplitLineCreate(amount=Decimal("50.00")),
        ]

        await service.split_transaction("tx-001", 2026, 4, splits, USER_ID, USER_NAME)

        replace_arg = mock_repo.replace.call_args[0][1]
        assert len(replace_arg["splits"]) == 2
        # Old split id should not be present
        new_ids = [s["id"] for s in replace_arg["splits"]]
        assert "split-old" not in new_ids
