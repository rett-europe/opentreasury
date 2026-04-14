"""Tests for the /api/audit, /api/me, and /api/reference-data routers."""

from unittest.mock import AsyncMock

from app.main import app
from app.repositories.dependencies import get_user_preferences_repo
from app.services.dependencies import (
    get_audit_service,
    get_reference_data_service,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_AUDIT_ENTRY = {
    "id": "audit-001",
    "entityType": "Transaction",
    "entityId": "tx-001",
    "action": "Create",
    "changedBy": "user-oid",
    "changedByName": "Test User",
    "changedAt": "2026-04-10T14:30:00Z",
    "oldValues": None,
    "newValues": {"amount": 150.50},
}

SAMPLE_ACCOUNT = {
    "id": "acc-001",
    "bankName": "TestBank",
    "bankNameShort": "TB",
    "iban": None,
    "paypalEmail": None,
    "accountLabel": "Main Account",
    "isPaypal": False,
    "currency": "EUR",
    "sortOrder": 0,
    "isActive": True,
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}

SAMPLE_CATEGORY = {
    "id": "cat-001",
    "name": "Donations",
    "description": None,
    "categoryType": "income",
    "sortOrder": 0,
    "isActive": True,
    "subcategories": [],
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}

SAMPLE_TAG = {
    "id": "tag-001",
    "name": "EU Grant",
    "color": None,
    "sortOrder": 0,
    "isActive": True,
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}


# ---------------------------------------------------------------------------
# GET /api/audit
# ---------------------------------------------------------------------------


class TestGetAuditTrail:
    async def test_returns_audit_list(self, admin_client):
        mock_audit = AsyncMock()
        mock_audit.query_trail.return_value = ([SAMPLE_AUDIT_ENTRY], None)
        app.dependency_overrides[get_audit_service] = lambda: mock_audit

        response = await admin_client.get("/api/audit")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "audit-001"

    async def test_with_filters(self, admin_client):
        mock_audit = AsyncMock()
        mock_audit.query_trail.return_value = ([SAMPLE_AUDIT_ENTRY], "next-token")
        app.dependency_overrides[get_audit_service] = lambda: mock_audit

        response = await admin_client.get("/api/audit?entityType=Transaction&entityId=tx-001&pageSize=10")

        assert response.status_code == 200
        data = response.json()
        assert data["continuationToken"] == "next-token"
        mock_audit.query_trail.assert_awaited_once_with(
            entity_type="Transaction",
            entity_id="tx-001",
            page_size=10,
            continuation_token=None,
        )

    async def test_viewer_forbidden(self, viewer_client):
        """Audit endpoint requires Admin role."""
        mock_audit = AsyncMock()
        app.dependency_overrides[get_audit_service] = lambda: mock_audit

        response = await viewer_client.get("/api/audit")

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/me
# ---------------------------------------------------------------------------


class TestGetCurrentUserProfile:
    async def test_returns_user_profile(self, admin_client):
        response = await admin_client.get("/api/me")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "testuser@example-ngo.org"
        assert data["role"] == "Admin"

    async def test_viewer_profile(self, viewer_client):
        response = await viewer_client.get("/api/me")

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "Viewer"


# ---------------------------------------------------------------------------
# GET /api/me/preferences
# ---------------------------------------------------------------------------


class TestGetUserPreferences:
    async def test_returns_defaults_when_no_stored_prefs(self, admin_client):
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        response = await admin_client.get("/api/me/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "es"
        assert data["theme"] == "light"
        assert data["compactMode"] is False
        assert data["reducedMotion"] is False

    async def test_returns_stored_preferences(self, admin_client):
        mock_repo = AsyncMock()
        mock_repo.get.return_value = {
            "id": "test-user-oid-abc123",
            "type": "user_preferences",
            "language": "en",
            "theme": "dark",
            "compactMode": True,
            "reducedMotion": True,
        }
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        response = await admin_client.get("/api/me/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["theme"] == "dark"
        assert data["compactMode"] is True
        assert data["reducedMotion"] is True

    async def test_viewer_can_get_preferences(self, viewer_client):
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        response = await viewer_client.get("/api/me/preferences")

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# PUT /api/me/preferences
# ---------------------------------------------------------------------------


class TestUpdateUserPreferences:
    async def test_saves_and_returns_preferences(self, admin_client):
        mock_repo = AsyncMock()
        mock_repo.upsert.return_value = None
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        payload = {
            "language": "en",
            "theme": "dark",
            "compactMode": True,
            "reducedMotion": False,
        }
        response = await admin_client.put("/api/me/preferences", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["theme"] == "dark"
        assert data["compactMode"] is True
        assert data["reducedMotion"] is False

        mock_repo.upsert.assert_awaited_once()

    async def test_defaults_applied_for_missing_fields(self, admin_client):
        mock_repo = AsyncMock()
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        response = await admin_client.put("/api/me/preferences", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "es"
        assert data["theme"] == "light"
        assert data["compactMode"] is False
        assert data["reducedMotion"] is False

    async def test_viewer_can_update_preferences(self, viewer_client):
        mock_repo = AsyncMock()
        app.dependency_overrides[get_user_preferences_repo] = lambda: mock_repo

        response = await viewer_client.put("/api/me/preferences", json={"language": "en"})

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/reference-data
# ---------------------------------------------------------------------------


class TestGetReferenceData:
    async def test_returns_all_reference_data(self, admin_client):
        mock_ref_svc = AsyncMock()
        mock_ref_svc.get_all.return_value = {
            "accounts": [SAMPLE_ACCOUNT],
            "categories": [SAMPLE_CATEGORY],
            "tags": [SAMPLE_TAG],
        }
        app.dependency_overrides[get_reference_data_service] = lambda: mock_ref_svc

        response = await admin_client.get("/api/reference-data")

        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 1
        assert len(data["categories"]) == 1
        assert len(data["tags"]) == 1

    async def test_empty_reference_data(self, admin_client):
        mock_ref_svc = AsyncMock()
        mock_ref_svc.get_all.return_value = {
            "accounts": [],
            "categories": [],
            "tags": [],
        }
        app.dependency_overrides[get_reference_data_service] = lambda: mock_ref_svc

        response = await admin_client.get("/api/reference-data")

        assert response.status_code == 200
        data = response.json()
        assert data["accounts"] == []
        assert data["categories"] == []
        assert data["tags"] == []
