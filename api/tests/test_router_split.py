"""Tests for the split transaction HTTP API endpoints.

Endpoints tested:
- POST   /api/transactions/{id}/split?year=YYYY&month=MM
- PUT    /api/transactions/{id}/split?year=YYYY&month=MM
- DELETE /api/transactions/{id}/split?year=YYYY&month=MM
"""

from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_split_service

# ---------------------------------------------------------------------------
# Sample data (camelCase — matches TransactionResponse + split fields)
# ---------------------------------------------------------------------------

SAMPLE_TX_UNSPLIT = {
    "id": "tx-abc12345",
    "date": "2026-04-10",
    "valueDate": "2026-04-10",
    "year": 2026,
    "month": 4,
    "partitionKey": "2026-04",
    "amount": -150.50,
    "currency": "EUR",
    "balance": None,
    "movementNumber": None,
    "branchNumber": None,
    "bankDescription": None,
    "accountId": "acc-001",
    "transactionType": "expense",
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
    "isSplit": False,
    "splitCount": 0,
    "splitLines": [],
    "splitCategoryIds": [],
}

SAMPLE_TX_SPLIT = {
    **SAMPLE_TX_UNSPLIT,
    "isSplit": True,
    "splitCount": 2,
    "categoryId": None,
    "subcategoryId": None,
    "splitCategoryIds": ["cat-alquiler", "cat-material"],
    "splitLines": [
        {
            "id": "sl-001",
            "amount": -100.50,
            "categoryId": "cat-alquiler",
            "subcategoryId": None,
            "tagIds": [],
            "detail": "Rent",
            "sortOrder": 1,
        },
        {
            "id": "sl-002",
            "amount": -50.00,
            "categoryId": "cat-material",
            "subcategoryId": None,
            "tagIds": [],
            "detail": "Office supplies",
            "sortOrder": 2,
        },
    ],
}

SPLIT_CREATE_PAYLOAD = {
    "lines": [
        {"amount": 100.50, "categoryId": "cat-alquiler", "detail": "Rent"},
        {"amount": 50.00, "categoryId": "cat-material", "detail": "Office supplies"},
    ]
}


@pytest.fixture
def mock_split_svc():
    svc = AsyncMock()
    svc.split_transaction.return_value = SAMPLE_TX_SPLIT
    svc.update_split.return_value = SAMPLE_TX_SPLIT
    svc.unsplit_transaction.return_value = SAMPLE_TX_UNSPLIT
    return svc


# ---------------------------------------------------------------------------
# POST /api/transactions/{id}/split — create split
# ---------------------------------------------------------------------------


class TestCreateSplit:
    async def test_create_split_returns_201(self, admin_client, mock_split_svc):
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["isSplit"] is True
        assert data["splitCount"] == 2
        assert len(data["splitLines"]) == 2

    async def test_create_split_response_includes_split_line_fields(self, admin_client, mock_split_svc):
        """Verify split lines have id, amount, categoryId, etc."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 201
        line = response.json()["splitLines"][0]
        assert "id" in line
        assert "amount" in line
        assert "categoryId" in line
        assert "sortOrder" in line

    async def test_create_split_validation_error_returns_422(self, admin_client, mock_split_svc):
        """Service ValueError maps to 422."""
        mock_split_svc.split_transaction.side_effect = ValueError("Sum of split lines does not match parent amount")
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 422

    async def test_create_split_too_few_lines_returns_422(self, admin_client, mock_split_svc):
        """Pydantic validation: lines must have min_length=2."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        payload = {"lines": [{"amount": 150.50}]}

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=payload,
        )

        # Either pydantic rejects (422) or service raises ValueError (422)
        assert response.status_code == 422

    async def test_create_split_not_found_returns_404(self, admin_client, mock_split_svc):
        """Transaction not found → 404."""
        mock_split_svc.split_transaction.return_value = None
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-nonexistent/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 404

    async def test_create_split_viewer_returns_403(self, viewer_client, mock_split_svc):
        """Viewer role cannot create splits (Admin only)."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await viewer_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/transactions/{id}/split — update split
# ---------------------------------------------------------------------------


class TestUpdateSplit:
    async def test_update_split_returns_200(self, admin_client, mock_split_svc):
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.put(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isSplit"] is True
        assert len(data["splitLines"]) == 2

    async def test_update_split_validation_error_returns_422(self, admin_client, mock_split_svc):
        """Service ValueError on update maps to 422."""
        mock_split_svc.update_split.side_effect = ValueError("Sum of split lines does not match parent amount")
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.put(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 422

    async def test_update_split_not_found_returns_404(self, admin_client, mock_split_svc):
        """Non-existent or non-split transaction → 404."""
        mock_split_svc.update_split.return_value = None
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.put(
            "/api/transactions/tx-nonexistent/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 404

    async def test_update_split_viewer_returns_403(self, viewer_client, mock_split_svc):
        """Viewer role cannot update splits (Admin only)."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await viewer_client.put(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/transactions/{id}/split — unsplit
# ---------------------------------------------------------------------------


class TestUnsplit:
    async def test_unsplit_returns_200(self, admin_client, mock_split_svc):
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.delete(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isSplit"] is False
        assert data["splitCount"] == 0
        assert data["splitLines"] == []

    async def test_unsplit_not_found_returns_404(self, admin_client, mock_split_svc):
        """Non-existent or non-split transaction → 404."""
        mock_split_svc.unsplit_transaction.return_value = None
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.delete(
            "/api/transactions/tx-nonexistent/split?year=2026&month=4",
        )

        assert response.status_code == 404

    async def test_unsplit_viewer_returns_403(self, viewer_client, mock_split_svc):
        """Viewer role cannot unsplit (Admin only)."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await viewer_client.delete(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
        )

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Response format verification
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Verify TransactionResponse includes split fields."""

    async def test_split_response_has_is_split_field(self, admin_client, mock_split_svc):
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        data = response.json()
        assert "isSplit" in data
        assert "splitCount" in data
        assert "splitLines" in data
        assert "splitCategoryIds" in data

    async def test_split_lines_structure(self, admin_client, mock_split_svc):
        """Each split line should have the required fields."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.post(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
            json=SPLIT_CREATE_PAYLOAD,
        )

        lines = response.json()["splitLines"]
        assert len(lines) >= 2
        for line in lines:
            assert "id" in line
            assert "amount" in line
            assert "sortOrder" in line
            # Optional fields should be present (even if null)
            assert "categoryId" in line
            assert "tagIds" in line

    async def test_unsplit_response_shows_cleared_split_data(self, admin_client, mock_split_svc):
        """After unsplit, response should show isSplit=false, empty splitLines."""
        app.dependency_overrides[get_split_service] = lambda: mock_split_svc

        response = await admin_client.delete(
            "/api/transactions/tx-abc12345/split?year=2026&month=4",
        )

        data = response.json()
        assert data["isSplit"] is False
        assert data["splitCount"] == 0
        assert data["splitLines"] == []
