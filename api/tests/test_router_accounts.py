"""Tests for the /api/accounts router."""

from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_account_service

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

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


@pytest.fixture
def mock_account_svc():
    svc = AsyncMock()
    svc.list_accounts.return_value = [SAMPLE_ACCOUNT]
    svc.get_account.return_value = SAMPLE_ACCOUNT
    svc.create_account.return_value = SAMPLE_ACCOUNT
    svc.update_account.return_value = SAMPLE_ACCOUNT
    svc.delete_account.return_value = True
    return svc


@pytest.fixture
def mock_txn_svc():
    svc = AsyncMock()
    svc.count_by_account.return_value = 0
    return svc


# ---------------------------------------------------------------------------
# GET /api/accounts
# ---------------------------------------------------------------------------


class TestListAccounts:
    async def test_returns_list(self, admin_client, mock_account_svc):
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.get("/api/accounts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "acc-aabbccdd1122"


# ---------------------------------------------------------------------------
# POST /api/accounts
# ---------------------------------------------------------------------------


class TestCreateAccount:
    async def test_creates_and_returns_201(self, admin_client, mock_account_svc):
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        payload = {
            "bankName": "Banco BPI",
            "accountLabel": "Conta principal",
        }
        response = await admin_client.post("/api/accounts", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "acc-aabbccdd1122"


# ---------------------------------------------------------------------------
# GET /api/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestGetAccount:
    async def test_found(self, admin_client, mock_account_svc):
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.get("/api/accounts/acc-aabbccdd1122")

        assert response.status_code == 200
        assert response.json()["id"] == "acc-aabbccdd1122"

    async def test_not_found(self, admin_client, mock_account_svc):
        mock_account_svc.get_account.return_value = None
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.get("/api/accounts/acc-nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestUpdateAccount:
    async def test_updated(self, admin_client, mock_account_svc):
        updated = {**SAMPLE_ACCOUNT, "bankName": "Novo Banco"}
        mock_account_svc.update_account.return_value = updated
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.put(
            "/api/accounts/acc-aabbccdd1122",
            json={"bankName": "Novo Banco"},
        )

        assert response.status_code == 200
        assert response.json()["bankName"] == "Novo Banco"

    async def test_not_found(self, admin_client, mock_account_svc):
        mock_account_svc.update_account.return_value = None
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.put(
            "/api/accounts/acc-nonexistent",
            json={"bankName": "X"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/accounts/{account_id}
# ---------------------------------------------------------------------------


class TestDeleteAccount:
    async def test_deleted(self, admin_client, mock_account_svc):
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.delete("/api/accounts/acc-aabbccdd1122")

        assert response.status_code == 204

    async def test_conflict_has_transactions(self, admin_client, mock_account_svc):
        mock_account_svc.delete_account.side_effect = ValueError(
            "Cannot delete account: 5 transaction(s) reference it. Deactivate instead."
        )
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.delete("/api/accounts/acc-aabbccdd1122")

        assert response.status_code == 409

    async def test_not_found(self, admin_client, mock_account_svc):
        mock_account_svc.delete_account.return_value = False
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.delete("/api/accounts/acc-nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# FR-002: Account currency (router level)
# ---------------------------------------------------------------------------


class TestAccountCurrency:
    async def test_create_with_explicit_currency(self, admin_client, mock_account_svc):
        """AC-002.1: currency stored when provided."""
        account_with_usd = {**SAMPLE_ACCOUNT, "currency": "USD"}
        mock_account_svc.create_account.return_value = account_with_usd
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        payload = {
            "bankName": "Banco BPI",
            "accountLabel": "USD Account",
            "currency": "USD",
        }
        response = await admin_client.post("/api/accounts", json=payload)

        assert response.status_code == 201
        assert response.json()["currency"] == "USD"

    async def test_create_defaults_to_eur(self, admin_client, mock_account_svc):
        """AC-002.2: currency defaults to EUR."""
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        payload = {
            "bankName": "Banco BPI",
            "accountLabel": "Conta principal",
        }
        response = await admin_client.post("/api/accounts", json=payload)

        assert response.status_code == 201
        assert response.json()["currency"] == "EUR"

    async def test_update_currency(self, admin_client, mock_account_svc):
        """AC-002.3: currency updateable."""
        updated_account = {**SAMPLE_ACCOUNT, "currency": "USD"}
        mock_account_svc.update_account.return_value = updated_account
        app.dependency_overrides[get_account_service] = lambda: mock_account_svc

        response = await admin_client.put(
            "/api/accounts/acc-aabbccdd1122",
            json={"currency": "USD"},
        )

        assert response.status_code == 200
        assert response.json()["currency"] == "USD"
