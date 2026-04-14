"""Tests for TagService — business logic with mocked repository."""

from unittest.mock import AsyncMock

import pytest

from app.models.domain import AuditAction
from app.models.schemas import TagCreate, TagUpdate
from app.services.tag_service import TagService

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
    repo.count_by_tag.return_value = 0
    return repo


@pytest.fixture
def service(mock_repo, mock_audit, mock_txn_repo):
    return TagService(repo=mock_repo, audit_service=mock_audit, transaction_repo=mock_txn_repo)


USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"

SAMPLE_TAG = {
    "id": "tag-aabbccdd1122",
    "type": "tag",
    "name": "Urgente",
    "color": "#FF0000",
    "sortOrder": 1,
    "isActive": True,
    "createdAt": "2026-04-01T10:00:00Z",
    "updatedAt": None,
}


# ---------------------------------------------------------------------------
# list_tags
# ---------------------------------------------------------------------------


class TestListTags:
    async def test_delegates_with_partition_key(self, service, mock_repo):
        mock_repo.list_all.return_value = [SAMPLE_TAG]

        result = await service.list_tags()

        assert result == [SAMPLE_TAG]
        mock_repo.list_all.assert_awaited_once_with("tag")


# ---------------------------------------------------------------------------
# create_tag
# ---------------------------------------------------------------------------


class TestCreateTag:
    async def test_builds_doc_with_tag_prefix(self, service, mock_repo, mock_audit):
        data = TagCreate(name="Urgente", color="#FF0000", sort_order=1)
        mock_repo.create.return_value = {**SAMPLE_TAG, "id": "tag-new123"}

        result = await service.create_tag(data, USER_ID, USER_NAME)

        assert result["id"] == "tag-new123"

        call_args = mock_repo.create.call_args
        doc = call_args[0][0]
        partition = call_args[0][1]

        assert partition == "tag"
        assert doc["type"] == "tag"
        assert doc["id"].startswith("tag-")
        assert doc["name"] == "Urgente"
        assert doc["name"] == "Urgente"
        assert doc["color"] == "#FF0000"
        assert doc["color"] == "#FF0000"
        assert doc["isActive"] is True

    async def test_calls_audit(self, service, mock_repo, mock_audit):
        data = TagCreate(name="Urgente", sort_order=0)
        mock_repo.create.return_value = {"id": "tag-new123"}

        await service.create_tag(data, USER_ID, USER_NAME)

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["entity_type"] == "Tag"
        assert audit_call.kwargs["action"] == AuditAction.CREATE
        assert audit_call.kwargs["new_values"] == {"name": "Urgente"}


# ---------------------------------------------------------------------------
# update_tag
# ---------------------------------------------------------------------------


class TestUpdateTag:
    async def test_tracks_changes(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = {**SAMPLE_TAG}
        mock_repo.replace.return_value = {**SAMPLE_TAG, "name": "Prioritário"}

        data = TagUpdate(name="Prioritário")

        result = await service.update_tag("tag-aabbccdd1122", data, USER_ID, USER_NAME)

        assert result is not None

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["action"] == AuditAction.UPDATE
        assert audit_call.kwargs["old_values"] == {"name": "Urgente"}
        assert audit_call.kwargs["new_values"] == {"name": "Prioritário"}

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        data = TagUpdate(name="Ghost")

        result = await service.update_tag("tag-nonexistent", data, USER_ID, USER_NAME)

        assert result is None
        mock_repo.replace.assert_not_awaited()
        mock_audit.log.assert_not_awaited()

    async def test_no_audit_when_no_changes(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = {**SAMPLE_TAG}
        mock_repo.replace.return_value = {**SAMPLE_TAG}

        data = TagUpdate(name="Urgente")  # same as existing

        await service.update_tag("tag-aabbccdd1122", data, USER_ID, USER_NAME)

        mock_audit.log.assert_not_awaited()


# ---------------------------------------------------------------------------
# delete_tag
# ---------------------------------------------------------------------------


class TestDeleteTag:
    async def test_delegates(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = SAMPLE_TAG

        result = await service.delete_tag("tag-aabbccdd1122", USER_ID, USER_NAME)

        assert result is True
        mock_repo.delete.assert_awaited_once_with("tag-aabbccdd1122", "tag")
        mock_audit.log.assert_awaited_once()

    async def test_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        result = await service.delete_tag("tag-nonexistent", USER_ID, USER_NAME)

        assert result is False
        mock_repo.delete.assert_not_awaited()

    async def test_conflict_raises_value_error(self, service, mock_txn_repo):
        mock_txn_repo.count_by_tag.return_value = 3

        with pytest.raises(ValueError, match="Cannot delete tag"):
            await service.delete_tag("tag-aabbccdd1122", USER_ID, USER_NAME)
