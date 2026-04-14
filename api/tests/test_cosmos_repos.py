"""
Unit tests for the Cosmos DB repository implementations.

These tests mock app.services.cosmos_client.cosmos_service so that no real
Azure connection is made.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from tests.conftest import AsyncIteratorMock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_container() -> MagicMock:
    """
    Container mock where:
    - query_items is a regular MagicMock (returns an async iterable, not a coroutine)
    - read/write methods are AsyncMock (awaitable)
    """
    container = MagicMock()
    container.read_item = AsyncMock()
    container.create_item = AsyncMock()
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    return container


def make_paged_mock(items: list, continuation_token=None) -> MagicMock:
    """Create a mock pager returned by query_items(...).by_page(...)."""
    page = AsyncIteratorMock(items)
    pager_mock = MagicMock()
    pager_mock.continuation_token = continuation_token

    async def aiter_pager(self_):
        yield page

    pager_mock.__aiter__ = lambda self_: aiter_pager(self_).__aiter__()
    return pager_mock


# ---------------------------------------------------------------------------
# CosmosTransactionRepository
# ---------------------------------------------------------------------------


class TestCosmosTransactionRepository:
    @pytest.fixture(autouse=True)
    def patch_cosmos(self):
        self.mock_container = make_mock_container()
        with patch("app.repositories.cosmos.transaction_repo.cosmos_service") as mock_svc:
            mock_svc.transactions = self.mock_container
            yield mock_svc

    @pytest.fixture
    def repo(self):
        from app.repositories.cosmos.transaction_repo import CosmosTransactionRepository

        return CosmosTransactionRepository()

    async def test_get_by_id_found(self, repo):
        self.mock_container.read_item.return_value = {"id": "tx-001"}
        result = await repo.get_by_id("tx-001", "2026-04")
        assert result["id"] == "tx-001"

    async def test_get_by_id_not_found_returns_none(self, repo):
        self.mock_container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        result = await repo.get_by_id("tx-nonexistent", "2026-04")
        assert result is None

    async def test_create(self, repo):
        doc = {"id": "tx-new", "partitionKey": "2026-04"}
        self.mock_container.create_item.return_value = doc
        result = await repo.create(doc)
        assert result["id"] == "tx-new"
        self.mock_container.create_item.assert_awaited_once_with(body=doc)

    async def test_replace(self, repo):
        doc = {"id": "tx-001", "amount": 200.0}
        self.mock_container.replace_item.return_value = doc
        result = await repo.replace("tx-001", doc)
        assert result["amount"] == 200.0
        self.mock_container.replace_item.assert_awaited_once_with(item="tx-001", body=doc)

    async def test_list_by_partition_no_filters(self, repo):
        sample_item = {"id": "tx-001"}
        pager_mock = make_paged_mock([sample_item], continuation_token="next-token")
        self.mock_container.query_items.return_value.by_page.return_value = pager_mock
        items, token = await repo.list_by_partition("2026-04")
        assert items == [sample_item]
        assert token == "next-token"

    async def test_list_by_partition_with_filters(self, repo):
        pager_mock = make_paged_mock([])
        self.mock_container.query_items.return_value.by_page.return_value = pager_mock
        filters = {
            "accountId": "acc-001",
            "categoryId": "cat-001",
            "subcategoryId": "subcat-001",
            "tagId": "tag-001",
            "search": "donation",
            "amountMin": 10.0,
            "amountMax": 500.0,
        }
        items, token = await repo.list_by_partition("2026-04", filters=filters, include_deleted=True)
        assert items == []
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert "@accountId" in str(call_kwargs["parameters"])
        assert "@search" in str(call_kwargs["parameters"])

    async def test_query_for_report_annual(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock(
            [{"categoryId": "cat-001", "amount": 100.0, "month": 4}]
        )
        items = await repo.query_for_report(year=2026)
        assert len(items) == 1

    async def test_query_for_report_monthly(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock(
            [{"categoryId": "cat-001", "amount": 100.0, "month": 4}]
        )
        items = await repo.query_for_report(year=2026, month=4)
        assert len(items) == 1

    async def test_query_for_report_with_account_filter(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([])
        items = await repo.query_for_report(year=2026, account_id="acc-001")
        assert items == []
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert "@accountId" in str(call_kwargs["parameters"])

    async def test_query_for_export(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([{"id": "tx-001"}])
        items = await repo.query_for_export("2026-04-01", "2026-04-30")
        assert len(items) == 1

    async def test_query_for_export_with_filters(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([])
        items = await repo.query_for_export("2026-01-01", "2026-12-31", account_id="acc-001", category_id="cat-001")
        assert items == []
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert "@accountId" in str(call_kwargs["parameters"])
        assert "@categoryId" in str(call_kwargs["parameters"])

    async def test_count_by_account(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([3])
        count = await repo.count_by_account("acc-001")
        assert count == 3

    async def test_count_by_category(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([5])
        count = await repo.count_by_category("cat-001")
        assert count == 5

    async def test_count_by_subcategory(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([2])
        count = await repo.count_by_subcategory("cat-001", "subcat-001")
        assert count == 2

    async def test_count_by_tag(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([1])
        count = await repo.count_by_tag("tag-001")
        assert count == 1

    async def test_query_for_report_monthly_with_account_filter(self, repo):
        """Covers the branch: monthly query WITH account_id filter (lines 87-88)."""
        self.mock_container.query_items.return_value = AsyncIteratorMock([])
        items = await repo.query_for_report(year=2026, month=4, account_id="acc-001")
        assert items == []
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert "@accountId" in str(call_kwargs["parameters"])
        assert call_kwargs.get("partition_key") == "2026-04"


# ---------------------------------------------------------------------------
# CosmosCategoryRepository
# ---------------------------------------------------------------------------


class TestCosmosCategoryRepository:
    @pytest.fixture(autouse=True)
    def patch_cosmos(self):
        self.mock_container = make_mock_container()
        with patch("app.repositories.cosmos.category_repo.cosmos_service") as mock_svc:
            mock_svc.categories = self.mock_container
            yield mock_svc

    @pytest.fixture
    def repo(self):
        from app.repositories.cosmos.category_repo import CosmosCategoryRepository

        return CosmosCategoryRepository()

    async def test_list_all(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([{"id": "cat-001", "name": "Donations"}])
        result = await repo.list_all()
        assert len(result) == 1
        assert result[0]["id"] == "cat-001"

    async def test_get_by_id_found(self, repo):
        self.mock_container.read_item.return_value = {"id": "cat-001"}
        result = await repo.get_by_id("cat-001")
        assert result["id"] == "cat-001"

    async def test_get_by_id_not_found(self, repo):
        self.mock_container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        result = await repo.get_by_id("cat-nonexistent")
        assert result is None

    async def test_create(self, repo):
        doc = {"id": "cat-new", "name": "New Category"}
        self.mock_container.create_item.return_value = doc
        result = await repo.create(doc)
        assert result["id"] == "cat-new"

    async def test_replace(self, repo):
        doc = {"id": "cat-001", "name": "Updated"}
        self.mock_container.replace_item.return_value = doc
        result = await repo.replace("cat-001", doc)
        assert result["name"] == "Updated"

    async def test_delete(self, repo):
        await repo.delete("cat-001")
        self.mock_container.delete_item.assert_awaited_once_with(item="cat-001", partition_key="cat-001")


# ---------------------------------------------------------------------------
# CosmosReferenceItemRepository
# ---------------------------------------------------------------------------


class TestCosmosReferenceItemRepository:
    @pytest.fixture(autouse=True)
    def patch_cosmos(self):
        self.mock_container = make_mock_container()
        with patch("app.repositories.cosmos.reference_item_repo.cosmos_service") as mock_svc:
            mock_svc.reference_data = self.mock_container
            yield mock_svc

    @pytest.fixture
    def repo(self):
        from app.repositories.cosmos.reference_item_repo import CosmosReferenceItemRepository

        return CosmosReferenceItemRepository()

    async def test_list_all(self, repo):
        self.mock_container.query_items.return_value = AsyncIteratorMock([{"id": "acc-001", "type": "bank_account"}])
        result = await repo.list_all("bank_account")
        assert len(result) == 1

    async def test_get_by_id_found_correct_type(self, repo):
        self.mock_container.read_item.return_value = {"id": "acc-001", "type": "bank_account"}
        result = await repo.get_by_id("acc-001", "bank_account")
        assert result["id"] == "acc-001"

    async def test_get_by_id_wrong_type_returns_none(self, repo):
        self.mock_container.read_item.return_value = {"id": "acc-001", "type": "tag"}
        result = await repo.get_by_id("acc-001", "bank_account")
        assert result is None

    async def test_get_by_id_exception_returns_none(self, repo):
        self.mock_container.read_item.side_effect = CosmosResourceNotFoundError(message="not found")
        result = await repo.get_by_id("acc-nonexistent", "bank_account")
        assert result is None

    async def test_create(self, repo):
        doc = {"id": "acc-new", "type": "bank_account"}
        self.mock_container.create_item.return_value = doc
        result = await repo.create(doc, "bank_account")
        assert result["id"] == "acc-new"

    async def test_replace(self, repo):
        doc = {"id": "acc-001", "type": "bank_account", "bankName": "NewBank"}
        self.mock_container.replace_item.return_value = doc
        result = await repo.replace("acc-001", doc, "bank_account")
        assert result["bankName"] == "NewBank"

    async def test_delete(self, repo):
        await repo.delete("acc-001", "bank_account")
        self.mock_container.delete_item.assert_awaited_once_with(item="acc-001", partition_key="bank_account")


# ---------------------------------------------------------------------------
# CosmosAuditRepository
# ---------------------------------------------------------------------------


class TestCosmosAuditRepository:
    @pytest.fixture(autouse=True)
    def patch_cosmos(self):
        self.mock_container = make_mock_container()
        with patch("app.repositories.cosmos.audit_repo.cosmos_service") as mock_svc:
            mock_svc.audit_log = self.mock_container
            yield mock_svc

    @pytest.fixture
    def repo(self):
        from app.repositories.cosmos.audit_repo import CosmosAuditRepository

        return CosmosAuditRepository()

    async def test_create_audit_entry(self, repo):
        entry = {"id": "audit-001", "entityType": "Transaction"}
        await repo.create(entry)
        self.mock_container.create_item.assert_awaited_once_with(body=entry)

    async def test_query_trail_no_filters(self, repo):
        sample = {"id": "audit-001"}
        pager_mock = make_paged_mock([sample])
        self.mock_container.query_items.return_value.by_page.return_value = pager_mock
        items, token = await repo.query_trail()
        assert items == [sample]
        assert token is None

    async def test_query_trail_with_entity_type_filter(self, repo):
        pager_mock = make_paged_mock([], continuation_token="next")
        self.mock_container.query_items.return_value.by_page.return_value = pager_mock
        items, token = await repo.query_trail(entity_type="Transaction")
        assert token == "next"
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert call_kwargs.get("partition_key") == "Transaction"

    async def test_query_trail_with_entity_id_filter(self, repo):
        pager_mock = make_paged_mock([])
        self.mock_container.query_items.return_value.by_page.return_value = pager_mock
        items, token = await repo.query_trail(entity_type="Transaction", entity_id="tx-001")
        assert items == []
        call_kwargs = self.mock_container.query_items.call_args[1]
        assert "@entityId" in str(call_kwargs["parameters"])
