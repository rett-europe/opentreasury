"""Tests for the /api/categories router."""

from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_category_service, get_transaction_service

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_CATEGORY = {
    "id": "cat-001",
    "type": "category",
    "name": "Donations",
    "description": "Income from donors",
    "categoryType": "income",
    "sortOrder": 0,
    "isActive": True,
    "subcategories": [
        {"id": "subcat-001", "name": "Individual Donors", "isActive": True},
    ],
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}

CAT_CREATE_PAYLOAD = {
    "name": "Donations",
    "categoryType": "income",
}

CAT_UPDATE_PAYLOAD = {
    "name": "Updated Donations",
}


@pytest.fixture
def mock_category_svc():
    svc = AsyncMock()
    svc.list_categories.return_value = [SAMPLE_CATEGORY]
    svc.get_category.return_value = SAMPLE_CATEGORY
    svc.create_category.return_value = SAMPLE_CATEGORY
    svc.update_category.return_value = SAMPLE_CATEGORY
    svc.delete_category.return_value = True
    svc.add_subcategory.return_value = SAMPLE_CATEGORY
    svc.update_subcategory.return_value = SAMPLE_CATEGORY
    svc.remove_subcategory.return_value = SAMPLE_CATEGORY
    return svc


@pytest.fixture
def mock_txn_svc():
    svc = AsyncMock()
    svc.count_by_category.return_value = 0
    svc.count_by_subcategory.return_value = 0
    return svc


@pytest.fixture
def mock_audit_svc():
    return AsyncMock()


# ---------------------------------------------------------------------------
# GET /api/categories
# ---------------------------------------------------------------------------


class TestListCategories:
    async def test_returns_list(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "cat-001"


# ---------------------------------------------------------------------------
# POST /api/categories
# ---------------------------------------------------------------------------


class TestCreateCategory:
    async def test_creates_returns_201(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.post("/api/categories", json=CAT_CREATE_PAYLOAD)

        assert response.status_code == 201
        assert response.json()["id"] == "cat-001"


# ---------------------------------------------------------------------------
# GET /api/categories/{category_id}
# ---------------------------------------------------------------------------


class TestGetCategory:
    async def test_found(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.get("/api/categories/cat-001")

        assert response.status_code == 200
        assert response.json()["id"] == "cat-001"

    async def test_not_found(self, admin_client, mock_category_svc):
        mock_category_svc.get_category.return_value = None
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.get("/api/categories/cat-nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/categories/{category_id}
# ---------------------------------------------------------------------------


class TestUpdateCategory:
    async def test_updated(self, admin_client, mock_category_svc, mock_txn_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.put("/api/categories/cat-001", json=CAT_UPDATE_PAYLOAD)

        assert response.status_code == 200

    async def test_not_found(self, admin_client, mock_category_svc, mock_txn_svc):
        mock_category_svc.update_category.return_value = None
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.put("/api/categories/cat-nonexistent", json=CAT_UPDATE_PAYLOAD)

        assert response.status_code == 404

    async def test_subcategory_removal_conflict(self, admin_client, mock_category_svc, mock_txn_svc):
        """Removing a subcategory that has transactions raises 409."""
        mock_txn_svc.count_by_subcategory.return_value = 3
        # Existing category has subcat-001 but the update removes it (empty list)
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        payload = {"subcategories": []}  # remove subcat-001
        response = await admin_client.put("/api/categories/cat-001", json=payload)

        assert response.status_code == 409

    async def test_update_without_subcategory_change(self, admin_client, mock_category_svc, mock_txn_svc):
        """Update with no subcategories field — no conflict check needed."""
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.put("/api/categories/cat-001", json={"name": "Renamed"})

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/categories/{category_id}
# ---------------------------------------------------------------------------


class TestDeleteCategory:
    async def test_deleted(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.delete("/api/categories/cat-001")

        assert response.status_code == 204

    async def test_conflict_has_transactions(self, admin_client, mock_category_svc):
        mock_category_svc.delete_category.side_effect = ValueError(
            "Cannot delete category: 3 transaction(s) reference it. Deactivate instead."
        )
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.delete("/api/categories/cat-001")

        assert response.status_code == 409

    async def test_not_found(self, admin_client, mock_category_svc):
        mock_category_svc.delete_category.return_value = False
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.delete("/api/categories/cat-nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/categories/{category_id}/subcategories
# ---------------------------------------------------------------------------


class TestAddSubcategory:
    async def test_adds_subcategory(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.post(
            "/api/categories/cat-001/subcategories",
            json={"name": "New Sub"},
        )

        assert response.status_code == 201

    async def test_category_not_found(self, admin_client, mock_category_svc):
        mock_category_svc.add_subcategory.return_value = None
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.post(
            "/api/categories/cat-nonexistent/subcategories",
            json={"name": "New Sub"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/categories/{category_id}/subcategories/{subcategory_id}
# ---------------------------------------------------------------------------


class TestUpdateSubcategory:
    async def test_updates_subcategory(self, admin_client, mock_category_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.put(
            "/api/categories/cat-001/subcategories/subcat-001",
            json={"name": "Updated Sub"},
        )

        assert response.status_code == 200

    async def test_not_found(self, admin_client, mock_category_svc):
        mock_category_svc.update_subcategory.return_value = None
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc

        response = await admin_client.put(
            "/api/categories/cat-001/subcategories/subcat-nonexistent",
            json={"name": "X"},
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/categories/{category_id}/subcategories/{subcategory_id}
# ---------------------------------------------------------------------------


class TestRemoveSubcategory:
    async def test_removed(self, admin_client, mock_category_svc, mock_txn_svc):
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.delete("/api/categories/cat-001/subcategories/subcat-001")

        assert response.status_code == 204

    async def test_conflict_has_transactions(self, admin_client, mock_category_svc, mock_txn_svc):
        mock_txn_svc.count_by_subcategory.return_value = 2
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.delete("/api/categories/cat-001/subcategories/subcat-001")

        assert response.status_code == 409

    async def test_not_found(self, admin_client, mock_category_svc, mock_txn_svc):
        mock_category_svc.remove_subcategory.return_value = None
        app.dependency_overrides[get_category_service] = lambda: mock_category_svc
        app.dependency_overrides[get_transaction_service] = lambda: mock_txn_svc

        response = await admin_client.delete("/api/categories/cat-001/subcategories/subcat-nonexistent")

        assert response.status_code == 404
