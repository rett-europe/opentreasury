"""Tests for the /api/transactions router."""

from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_transaction_service

# ---------------------------------------------------------------------------
# Sample data (matches TransactionResponse schema — camelCase keys)
# ---------------------------------------------------------------------------

SAMPLE_TX = {
    "id": "tx-abc12345",
    "date": "2026-04-10",
    "valueDate": "2026-04-10",
    "year": 2026,
    "month": 4,
    "partitionKey": "2026-04",
    "amount": 150.50,
    "currency": "EUR",
    "balance": None,
    "movementNumber": None,
    "branchNumber": None,
    "bankDescription": None,
    "accountId": "acc-001",
    "transactionType": "income",
    "categoryId": "cat-001",
    "subcategoryId": "subcat-001",
    "categorizationStatus": "manually_categorized",
    "sourceReference": None,
    "counterpartyName": None,
    "counterpartyReference": None,
    "reviewStatus": "approved",
    "reviewedBy": None,
    "reviewedByName": None,
    "reviewedAt": None,
    "originalAmount": None,
    "originalDate": None,
    "notes": [],
    "tagIds": [],
    "detail": None,
    "createdBy": "test-user-oid-abc123",
    "createdByName": "Test User",
    "createdAt": "2026-04-10T14:30:00Z",
    "updatedBy": None,
    "updatedByName": None,
    "updatedAt": None,
    "isDeleted": False,
}

TX_CREATE_PAYLOAD = {
    "date": "2026-04-10",
    "amount": 150.50,
    "accountId": "acc-001",
    "transactionType": "income",
    "categoryId": "cat-001",
    "subcategoryId": "subcat-001",
}


@pytest.fixture
def mock_txn_svc():
    svc = AsyncMock()
    svc.list_transactions.return_value = ([SAMPLE_TX], None, None)
    svc.get_transaction.return_value = SAMPLE_TX
    svc.create_transaction.return_value = SAMPLE_TX
    svc.update_transaction.return_value = SAMPLE_TX
    svc.soft_delete_transaction.return_value = True
    svc.review_transaction.return_value = SAMPLE_TX
    svc.categorize_transaction.return_value = SAMPLE_TX
    svc.add_note.return_value = SAMPLE_TX
    return svc


# ---------------------------------------------------------------------------
# GET /api/transactions
# ---------------------------------------------------------------------------


class TestListTransactions:
    async def test_returns_list(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions?year=2026&month=4")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1

    async def test_missing_required_params_returns_422(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions")

        assert response.status_code == 422

    async def test_non_admin_include_deleted_is_ignored(self, viewer_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await viewer_client.get("/api/transactions?year=2026&month=4&includeDeleted=true")

        assert response.status_code == 200
        # non-admin has include_deleted forced to False
        _, call_kwargs = mock_txn_svc.list_transactions.call_args
        assert call_kwargs.get("include_deleted") is False or (
            mock_txn_svc.list_transactions.call_args[1].get("include_deleted") is False
        )


# ---------------------------------------------------------------------------
# POST /api/transactions
# ---------------------------------------------------------------------------


class TestCreateTransaction:
    async def test_creates_returns_201(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post("/api/transactions", json=TX_CREATE_PAYLOAD)

        assert response.status_code == 201
        assert response.json()["id"] == "tx-abc12345"


# ---------------------------------------------------------------------------
# GET /api/transactions/{transaction_id}
# ---------------------------------------------------------------------------


class TestGetTransaction:
    async def test_found(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions/tx-abc12345?year=2026&month=4")

        assert response.status_code == 200
        assert response.json()["id"] == "tx-abc12345"

    async def test_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.get_transaction.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions/tx-nonexistent?year=2026&month=4")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/transactions/{transaction_id}
# ---------------------------------------------------------------------------


class TestUpdateTransaction:
    async def test_updated(self, admin_client, mock_txn_svc):
        updated = {**SAMPLE_TX, "amount": 200.0}
        mock_txn_svc.update_transaction.return_value = updated
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.put(
            "/api/transactions/tx-abc12345?year=2026&month=4",
            json={"amount": 200.0},
        )

        assert response.status_code == 200

    async def test_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.update_transaction.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.put(
            "/api/transactions/tx-nonexistent?year=2026&month=4",
            json={"amount": 50.0},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/transactions/{transaction_id}
# ---------------------------------------------------------------------------


class TestDeleteTransaction:
    async def test_deleted(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.delete("/api/transactions/tx-abc12345?year=2026&month=4")

        assert response.status_code == 204

    async def test_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.soft_delete_transaction.return_value = False
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.delete("/api/transactions/tx-nonexistent?year=2026&month=4")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/transactions/{transaction_id}/review
# ---------------------------------------------------------------------------


class TestReviewTransaction:
    async def test_review_returns_200(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.patch(
            "/api/transactions/tx-abc12345/review?year=2026&month=4",
            json={"reviewStatus": "reviewed"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "tx-abc12345"

    async def test_review_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.review_transaction.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.patch(
            "/api/transactions/tx-nonexistent/review?year=2026&month=4",
            json={"reviewStatus": "flagged"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/transactions/{transaction_id}/categorize
# ---------------------------------------------------------------------------


class TestCategorizeTransaction:
    async def test_categorize_returns_200(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.patch(
            "/api/transactions/tx-abc12345/categorize?year=2026&month=4",
            json={"categoryId": "cat-002", "subcategoryId": None},
        )

        assert response.status_code == 200

    async def test_categorize_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.categorize_transaction.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.patch(
            "/api/transactions/tx-nonexistent/categorize?year=2026&month=4",
            json={"categoryId": "cat-002"},
        )

        assert response.status_code == 404

    async def test_categorize_validation_error_returns_422(self, admin_client, mock_txn_svc):
        mock_txn_svc.categorize_transaction.side_effect = ValueError("Category type mismatch")
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.patch(
            "/api/transactions/tx-abc12345/categorize?year=2026&month=4",
            json={"categoryId": "cat-wrong"},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/transactions/{transaction_id}/notes
# ---------------------------------------------------------------------------


class TestAddNote:
    async def test_add_note_returns_201(self, admin_client, mock_txn_svc):
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/notes?year=2026&month=4",
            json={"text": "Test note"},
        )

        assert response.status_code == 201
        assert response.json()["id"] == "tx-abc12345"

    async def test_add_note_not_found(self, admin_client, mock_txn_svc):
        mock_txn_svc.add_note.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-nonexistent/notes?year=2026&month=4",
            json={"text": "Test note"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Schema validation (AC-010.1)
# ---------------------------------------------------------------------------


class TestCreateValidation:
    async def test_create_without_transaction_type_returns_422(self, admin_client, mock_txn_svc):
        """AC-010.1: transactionType is required — 422 without it."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        payload = {
            "date": "2026-04-10",
            "amount": 150.50,
            "accountId": "acc-001",
            # no transactionType
        }
        response = await admin_client.post("/api/transactions", json=payload)

        assert response.status_code == 422

    async def test_create_value_error_returns_422(self, admin_client, mock_txn_svc):
        """Service ValueError maps to 422."""
        mock_txn_svc.create_transaction.side_effect = ValueError("Subcategory does not belong to category")
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        payload = {
            "date": "2026-04-10",
            "amount": 150.50,
            "accountId": "acc-001",
            "transactionType": "expense",
            "categoryId": "cat-income",
            "subcategoryId": "sub-wrong",
        }
        response = await admin_client.post("/api/transactions", json=payload)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# List filters (AC-021.3, AC-034.2)
# ---------------------------------------------------------------------------


class TestListTransactionFilters:
    async def test_filter_by_review_status(self, admin_client, mock_txn_svc):
        """AC-034.2: filter by reviewStatus at router level."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions?year=2026&month=4&reviewStatus=pending")

        assert response.status_code == 200
        call_kwargs = mock_txn_svc.list_transactions.call_args.kwargs
        assert call_kwargs["review_status"] == "pending"

    async def test_filter_by_categorization_status(self, admin_client, mock_txn_svc):
        """AC-021.3: filter by categorizationStatus at router level."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions?year=2026&month=4&categorizationStatus=uncategorized")

        assert response.status_code == 200
        call_kwargs = mock_txn_svc.list_transactions.call_args.kwargs
        assert call_kwargs["categorization_status"] == "uncategorized"


# ---------------------------------------------------------------------------
# Notes in response (AC-033.3)
# ---------------------------------------------------------------------------


class TestNotesInResponse:
    async def test_notes_returned_in_get_response(self, admin_client, mock_txn_svc):
        """AC-033.3: notes returned in transaction response."""
        tx_with_notes = {
            **SAMPLE_TX,
            "notes": [
                {
                    "id": "note-001",
                    "text": "Test note",
                    "author": "test-oid",
                    "authorName": "Test User",
                    "createdAt": "2026-04-10T15:00:00Z",
                },
            ],
        }
        mock_txn_svc.get_transaction.return_value = tx_with_notes
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions/tx-abc12345?year=2026&month=4")

        assert response.status_code == 200
        data = response.json()
        assert len(data["notes"]) == 1
        assert data["notes"][0]["text"] == "Test note"
        assert data["notes"][0]["author"] == "test-oid"


# ---------------------------------------------------------------------------
# POST /api/transactions/{transaction_id}/split
# ---------------------------------------------------------------------------


SPLIT_PAYLOAD = {
    "splits": [
        {"amount": 100.00, "categoryId": "cat-001", "tagIds": [], "detail": "Part A"},
        {"amount": 50.50, "categoryId": "cat-001", "tagIds": [], "detail": "Part B"},
    ]
}

SPLIT_TX = {
    **SAMPLE_TX,
    "amount": -150.50,
    "transactionType": "expense",
    "isSplit": True,
    "splits": [
        {"id": "split-001", "amount": 100.00, "categoryId": "cat-001", "subcategoryId": None, "tagIds": [], "detail": "Part A"},
        {"id": "split-002", "amount": 50.50, "categoryId": "cat-001", "subcategoryId": None, "tagIds": [], "detail": "Part B"},
    ],
}


class TestSplitTransaction:
    async def test_split_returns_200(self, admin_client, mock_txn_svc):
        mock_txn_svc.split_transaction.return_value = SPLIT_TX
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_PAYLOAD,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isSplit"] is True
        assert len(data["splits"]) == 2

    async def test_split_not_found_returns_404(self, admin_client, mock_txn_svc):
        mock_txn_svc.split_transaction.return_value = None
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-missing/split?year=2026&month=4",
            json=SPLIT_PAYLOAD,
        )

        assert response.status_code == 404

    async def test_split_amount_mismatch_returns_422(self, admin_client, mock_txn_svc):
        mock_txn_svc.split_transaction.side_effect = ValueError("Split amounts total (80.00) must equal parent transaction amount (150.50)")
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        bad_payload = {
            "splits": [
                {"amount": 50.00, "tagIds": []},
                {"amount": 30.00, "tagIds": []},
            ]
        }
        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=bad_payload,
        )

        assert response.status_code == 422

    async def test_split_requires_at_least_two_lines(self, admin_client, mock_txn_svc):
        """SplitRequest requires min 2 split lines — schema rejects single item."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json={"splits": [{"amount": 150.50, "tagIds": []}]},
        )

        assert response.status_code == 422

    async def test_split_requires_positive_amounts(self, admin_client, mock_txn_svc):
        """Split line amounts must be > 0."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json={
                "splits": [
                    {"amount": 0.00, "tagIds": []},
                    {"amount": 150.50, "tagIds": []},
                ]
            },
        )

        assert response.status_code == 422

    async def test_split_viewer_forbidden(self, viewer_client, mock_txn_svc):
        """Non-admin users cannot split transactions."""
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await viewer_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_PAYLOAD,
        )

        assert response.status_code == 403

    async def test_split_response_contains_splits_field(self, admin_client, mock_txn_svc):
        """Response always contains splits array (empty for unsplit transactions)."""
        mock_txn_svc.get_transaction.return_value = SAMPLE_TX
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.get("/api/transactions/tx-abc12345?year=2026&month=4")

        assert response.status_code == 200
        data = response.json()
        assert "splits" in data
        assert data["splits"] == []
        assert "isSplit" in data
        assert data["isSplit"] is False
