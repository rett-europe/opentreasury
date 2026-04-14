"""Tests for the /api/tags router."""

from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.dependencies import get_tag_service

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_TAG = {
    "id": "tag-001",
    "type": "tag",
    "name": "EU Grant",
    "color": "#3B82F6",
    "sortOrder": 1,
    "isActive": True,
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}


@pytest.fixture
def mock_tag_svc():
    svc = AsyncMock()
    svc.list_tags.return_value = [SAMPLE_TAG]
    svc.get_tag.return_value = SAMPLE_TAG
    svc.create_tag.return_value = SAMPLE_TAG
    svc.update_tag.return_value = SAMPLE_TAG
    svc.delete_tag.return_value = True
    return svc


# ---------------------------------------------------------------------------
# GET /api/tags
# ---------------------------------------------------------------------------


class TestListTags:
    async def test_returns_list(self, admin_client, mock_tag_svc):
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.get("/api/tags")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "tag-001"


# ---------------------------------------------------------------------------
# POST /api/tags
# ---------------------------------------------------------------------------


class TestCreateTag:
    async def test_creates_returns_201(self, admin_client, mock_tag_svc):
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.post("/api/tags", json={"name": "EU Grant"})

        assert response.status_code == 201
        assert response.json()["id"] == "tag-001"


# ---------------------------------------------------------------------------
# GET /api/tags/{tag_id}
# ---------------------------------------------------------------------------


class TestGetTag:
    async def test_found(self, admin_client, mock_tag_svc):
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.get("/api/tags/tag-001")

        assert response.status_code == 200
        assert response.json()["id"] == "tag-001"

    async def test_not_found(self, admin_client, mock_tag_svc):
        mock_tag_svc.get_tag.return_value = None
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.get("/api/tags/tag-nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/tags/{tag_id}
# ---------------------------------------------------------------------------


class TestUpdateTag:
    async def test_updated(self, admin_client, mock_tag_svc):
        updated = {**SAMPLE_TAG, "name": "EU Grant Updated"}
        mock_tag_svc.update_tag.return_value = updated
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.put("/api/tags/tag-001", json={"name": "EU Grant Updated"})

        assert response.status_code == 200

    async def test_not_found(self, admin_client, mock_tag_svc):
        mock_tag_svc.update_tag.return_value = None
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.put("/api/tags/tag-nonexistent", json={"name": "X"})

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tags/{tag_id}
# ---------------------------------------------------------------------------


class TestDeleteTag:
    async def test_deleted(self, admin_client, mock_tag_svc):
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.delete("/api/tags/tag-001")

        assert response.status_code == 204

    async def test_conflict_has_transactions(self, admin_client, mock_tag_svc):
        mock_tag_svc.delete_tag.side_effect = ValueError(
            "Cannot delete tag: 3 transaction(s) reference it. Deactivate instead."
        )
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.delete("/api/tags/tag-001")

        assert response.status_code == 409

    async def test_not_found(self, admin_client, mock_tag_svc):
        mock_tag_svc.delete_tag.return_value = False
        app.dependency_overrides[get_tag_service] = lambda: mock_tag_svc

        response = await admin_client.delete("/api/tags/tag-nonexistent")

        assert response.status_code == 404
