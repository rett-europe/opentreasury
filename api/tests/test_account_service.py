"""Tests for AccountService — business logic with mocked repository."""

from unittest.mock import AsyncMock

import pytest

from app.models.domain import AuditAction
from app.models.schemas import AccountCreate, AccountUpdate
from app.services.account_service import AccountService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_audit():
    return AsyncMock()


@pytest.fixture
def mock_txn_repo():
    repo = AsyncMock()
    repo.count_by_account.return_value = 0
    return repo


@pytest.fixture
def service(mock_repo, mock_audit, mock_txn_repo):
    return AccountService(repo=mock_repo, audit_service=mock_audit, transaction_repo=mock_txn_repo)


USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"

SAMPLE_ACCOUNT = {
    "id": "acc-aabbccdd1122",
    "type": "bank_account",
    "bankName": "Banco BPI",
    "bankNameShort": "BPI",
    "iban": "PT50000201231234567890154",
    "paypalEmail": None,
    "accountLabel": "Conta principal",
    "isPaypal": False,
    "currency": "EUR",
    "sortOrder": 1,
    "isActive": True,
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}


# ---------------------------------------------------------------------------
# list_accounts
# ---------------------------------------------------------------------------


class TestListAccounts:
    async def test_delegates_with_partition_key(self, service, mock_repo):
        mock_repo.list_all.return_value = [SAMPLE_ACCOUNT]

        result = await service.list_accounts()

        assert result == [SAMPLE_ACCOUNT]
        mock_repo.list_all.assert_awaited_once_with("bank_account")


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------


class TestGetAccount:
    async def test_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = SAMPLE_ACCOUNT

        result = await service.get_account("acc-aabbccdd1122")

        assert result == SAMPLE_ACCOUNT
        mock_repo.get_by_id.assert_awaited_once_with("acc-aabbccdd1122", "bank_account")

    async def test_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None

        result = await service.get_account("acc-nonexistent")

        assert result is None


# ---------------------------------------------------------------------------
# create_account
# ---------------------------------------------------------------------------


class TestCreateAccount:
    async def test_builds_document(self, service, mock_repo, mock_audit):
        data = AccountCreate(
            bank_name="Banco BPI",
            bank_name_short="BPI",
            iban="PT50000201231234567890154",
            account_label="Conta principal",
            is_paypal=False,
            sort_order=1,
        )
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT, "id": "acc-new123"}

        result = await service.create_account(data, USER_ID, USER_NAME)

        assert result["id"] == "acc-new123"

        call_args = mock_repo.create.call_args
        doc = call_args[0][0]
        partition = call_args[0][1]

        assert partition == "bank_account"
        assert doc["type"] == "bank_account"
        assert doc["bankName"] == "Banco BPI"
        assert doc["bankNameShort"] == "BPI"
        assert doc["iban"] == "PT50000201231234567890154"
        assert doc["accountLabel"] == "Conta principal"
        assert doc["isPaypal"] is False
        assert doc["currency"] == "EUR"
        assert doc["isActive"] is True
        assert doc["id"].startswith("acc-")

    async def test_calls_audit(self, service, mock_repo, mock_audit):
        data = AccountCreate(
            bank_name="Banco BPI",
            account_label="Conta principal",
        )
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT, "id": "acc-new123"}

        await service.create_account(data, USER_ID, USER_NAME)

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["entity_type"] == "BankAccount"
        assert audit_call.kwargs["action"] == AuditAction.CREATE
        assert audit_call.kwargs["changed_by"] == USER_ID
        assert audit_call.kwargs["new_values"] == {"accountLabel": "Conta principal"}


# ---------------------------------------------------------------------------
# update_account
# ---------------------------------------------------------------------------


class TestUpdateAccount:
    async def test_tracks_changes(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = {**SAMPLE_ACCOUNT}
        mock_repo.replace.return_value = {**SAMPLE_ACCOUNT, "bankName": "Novo Banco"}

        data = AccountUpdate(bank_name="Novo Banco")

        result = await service.update_account("acc-aabbccdd1122", data, USER_ID, USER_NAME)

        assert result is not None

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["action"] == AuditAction.UPDATE
        assert audit_call.kwargs["old_values"] == {"bankName": "Banco BPI"}
        assert audit_call.kwargs["new_values"] == {"bankName": "Novo Banco"}

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        data = AccountUpdate(bank_name="Novo Banco")

        result = await service.update_account("acc-nonexistent", data, USER_ID, USER_NAME)

        assert result is None
        mock_repo.replace.assert_not_awaited()
        mock_audit.log.assert_not_awaited()

    async def test_no_audit_when_no_changes(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = {**SAMPLE_ACCOUNT}
        mock_repo.replace.return_value = {**SAMPLE_ACCOUNT}

        data = AccountUpdate(bank_name="Banco BPI")  # same as existing

        await service.update_account("acc-aabbccdd1122", data, USER_ID, USER_NAME)

        mock_audit.log.assert_not_awaited()


# ---------------------------------------------------------------------------
# delete_account
# ---------------------------------------------------------------------------


class TestDeleteAccount:
    async def test_delegates_to_repo(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = SAMPLE_ACCOUNT

        result = await service.delete_account("acc-aabbccdd1122", USER_ID, USER_NAME)

        assert result is True
        mock_repo.delete.assert_awaited_once_with("acc-aabbccdd1122", "bank_account")
        mock_audit.log.assert_awaited_once()

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        result = await service.delete_account("acc-nonexistent", USER_ID, USER_NAME)

        assert result is False
        mock_repo.delete.assert_not_awaited()

    async def test_conflict_raises_value_error(self, service, mock_txn_repo):
        mock_txn_repo.count_by_account.return_value = 3

        with pytest.raises(ValueError, match="Cannot delete account"):
            await service.delete_account("acc-aabbccdd1122", USER_ID, USER_NAME)


# ---------------------------------------------------------------------------
# FR-002: Account currency
# ---------------------------------------------------------------------------


class TestAccountCurrency:
    """FR-002: Account currency field tests."""

    async def test_create_with_explicit_currency(self, service, mock_repo, mock_audit):
        """AC-002.1: currency stored when provided."""
        data = AccountCreate(
            bank_name="Banco BPI",
            account_label="USD Account",
            currency="USD",
        )
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT, "currency": "USD", "id": "acc-new"}

        await service.create_account(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args
        doc = call_args[0][0]
        assert doc["currency"] == "USD"

    async def test_create_defaults_to_eur(self, service, mock_repo, mock_audit):
        """AC-002.2: currency defaults to EUR."""
        data = AccountCreate(
            bank_name="Banco BPI",
            account_label="Conta principal",
        )
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT, "id": "acc-new"}

        await service.create_account(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args
        doc = call_args[0][0]
        assert doc["currency"] == "EUR"

    async def test_update_currency(self, service, mock_repo, mock_audit):
        """AC-002.3: update currency."""
        mock_repo.get_by_id.return_value = {**SAMPLE_ACCOUNT}
        mock_repo.replace.return_value = {**SAMPLE_ACCOUNT, "currency": "USD"}

        data = AccountUpdate(currency="USD")
        result = await service.update_account("acc-aabbccdd1122", data, USER_ID, USER_NAME)

        assert result is not None
        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["old_values"] == {"currency": "EUR"}
        assert audit_call.kwargs["new_values"] == {"currency": "USD"}


# ---------------------------------------------------------------------------
# Issue #20: Account color
# ---------------------------------------------------------------------------


class TestAccountColor:
    """Issue #20: color code assigned to accounts from a fixed palette."""

    async def test_create_with_color(self, service, mock_repo, mock_audit):
        data = AccountCreate(
            bank_name="Banco BPI",
            account_label="Principal",
            color="#7BB3F0",
        )
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT, "color": "#7BB3F0"}

        await service.create_account(data, USER_ID, USER_NAME)

        doc = mock_repo.create.call_args[0][0]
        assert doc["color"] == "#7BB3F0"

    async def test_create_without_color_defaults_to_none(self, service, mock_repo, mock_audit):
        data = AccountCreate(bank_name="Banco BPI", account_label="Principal")
        mock_repo.create.return_value = {**SAMPLE_ACCOUNT}

        await service.create_account(data, USER_ID, USER_NAME)

        doc = mock_repo.create.call_args[0][0]
        assert doc["color"] is None

    def test_invalid_color_rejected(self):
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            AccountCreate(bank_name="X", account_label="Y", color="#123456")

    def test_color_is_normalized_to_uppercase(self):
        data = AccountCreate(bank_name="X", account_label="Y", color="#7bb3f0")
        assert data.color == "#7BB3F0"

    async def test_update_color(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = {**SAMPLE_ACCOUNT, "color": None}
        mock_repo.replace.return_value = {**SAMPLE_ACCOUNT, "color": "#A3D977"}

        data = AccountUpdate(color="#A3D977")
        result = await service.update_account("acc-aabbccdd1122", data, USER_ID, USER_NAME)

        assert result is not None
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["old_values"] == {"color": None}
        assert audit_call.kwargs["new_values"] == {"color": "#A3D977"}
