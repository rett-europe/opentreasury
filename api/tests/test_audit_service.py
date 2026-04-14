"""Tests for AuditService — business logic with mocked repository."""

from unittest.mock import AsyncMock

import pytest

from app.models.domain import AuditAction
from app.services.audit_service import AuditService

from .conftest import make_audit_entry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return AuditService(repo=mock_repo)


USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------


class TestLog:
    async def test_creates_entry_with_all_fields(self, service, mock_repo):
        await service.log(
            entity_type="Transaction",
            entity_id="tx-001",
            action=AuditAction.CREATE,
            changed_by=USER_ID,
            changed_by_name=USER_NAME,
            old_values={"amount": 100.0},
            new_values={"amount": 200.0},
        )

        mock_repo.create.assert_awaited_once()
        entry = mock_repo.create.call_args[0][0]

        assert entry["entityType"] == "Transaction"
        assert entry["entityId"] == "tx-001"
        assert entry["action"] == "Create"
        assert entry["changedBy"] == USER_ID
        assert entry["changedByName"] == USER_NAME
        assert entry["oldValues"] == {"amount": 100.0}
        assert entry["newValues"] == {"amount": 200.0}
        assert entry["ttl"] == 220752000  # ~7 years
        assert entry["id"] is not None
        assert entry["changedAt"] is not None

    async def test_defaults_empty_dicts(self, service, mock_repo):
        await service.log(
            entity_type="Category",
            entity_id="cat-001",
            action=AuditAction.DELETE,
            changed_by=USER_ID,
        )

        entry = mock_repo.create.call_args[0][0]
        assert entry["oldValues"] == {}
        assert entry["newValues"] == {}
        assert entry["changedByName"] == ""

    async def test_action_enum_stored_as_string(self, service, mock_repo):
        await service.log(
            entity_type="Tag",
            entity_id="tag-001",
            action=AuditAction.UPDATE,
            changed_by=USER_ID,
        )

        entry = mock_repo.create.call_args[0][0]
        assert entry["action"] == "Update"
        assert isinstance(entry["action"], str)


# ---------------------------------------------------------------------------
# query_trail
# ---------------------------------------------------------------------------


class TestQueryTrail:
    async def test_delegates_to_repo(self, service, mock_repo):
        entries = [make_audit_entry(), make_audit_entry()]
        mock_repo.query_trail.return_value = (entries, "next-tok")

        result_items, token = await service.query_trail(
            entity_type="Transaction",
            entity_id="tx-001",
            page_size=10,
            continuation_token=None,
        )

        assert result_items == entries
        assert token == "next-tok"
        mock_repo.query_trail.assert_awaited_once_with(
            entity_type="Transaction",
            entity_id="tx-001",
            page_size=10,
            continuation_token=None,
        )

    async def test_defaults(self, service, mock_repo):
        mock_repo.query_trail.return_value = ([], None)

        await service.query_trail()

        mock_repo.query_trail.assert_awaited_once_with(
            entity_type=None,
            entity_id=None,
            page_size=20,
            continuation_token=None,
        )
