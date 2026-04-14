"""
Tests for miscellaneous services and dependency wiring:
- ReferenceDataService
- services/dependencies.py factory functions
- repositories/dependencies.py factory functions
- CosmosService
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# ReferenceDataService
# ---------------------------------------------------------------------------


class TestReferenceDataService:
    @pytest.fixture
    def mock_account_svc(self):
        svc = AsyncMock()
        svc.list_accounts.return_value = [{"id": "acc-001"}]
        return svc

    @pytest.fixture
    def mock_category_svc(self):
        svc = AsyncMock()
        svc.list_categories.return_value = [{"id": "cat-001"}]
        return svc

    @pytest.fixture
    def mock_tag_svc(self):
        svc = AsyncMock()
        svc.list_tags.return_value = [{"id": "tag-001"}]
        return svc

    @pytest.fixture
    def service(self, mock_account_svc, mock_category_svc, mock_tag_svc):
        from app.services.reference_data_service import ReferenceDataService

        return ReferenceDataService(
            account_service=mock_account_svc,
            category_service=mock_category_svc,
            tag_service=mock_tag_svc,
        )

    async def test_get_all_returns_combined_data(self, service, mock_account_svc, mock_category_svc, mock_tag_svc):
        result = await service.get_all()

        assert result["accounts"] == [{"id": "acc-001"}]
        assert result["categories"] == [{"id": "cat-001"}]
        assert result["tags"] == [{"id": "tag-001"}]

    async def test_calls_all_services(self, service, mock_account_svc, mock_category_svc, mock_tag_svc):
        await service.get_all()

        mock_account_svc.list_accounts.assert_awaited_once()
        mock_category_svc.list_categories.assert_awaited_once()
        mock_tag_svc.list_tags.assert_awaited_once()


# ---------------------------------------------------------------------------
# services/dependencies.py factory functions
# ---------------------------------------------------------------------------


class TestServicesDependencies:
    def test_get_audit_service(self):
        from app.services.audit_service import AuditService
        from app.services.dependencies import get_audit_service

        mock_repo = AsyncMock()
        service = get_audit_service(repo=mock_repo)

        assert isinstance(service, AuditService)

    def test_get_transaction_service(self):
        from app.services.dependencies import get_transaction_service
        from app.services.transaction_service import TransactionService

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        mock_cat_repo = AsyncMock()
        service = get_transaction_service(repo=mock_repo, audit_service=mock_audit, category_repo=mock_cat_repo)

        assert isinstance(service, TransactionService)

    def test_get_account_service(self):
        from app.services.account_service import AccountService
        from app.services.dependencies import get_account_service

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = get_account_service(repo=mock_repo, audit_service=mock_audit)

        assert isinstance(service, AccountService)

    def test_get_tag_service(self):
        from app.services.dependencies import get_tag_service
        from app.services.tag_service import TagService

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = get_tag_service(repo=mock_repo, audit_service=mock_audit)

        assert isinstance(service, TagService)

    def test_get_category_service(self):
        from app.services.category_service import CategoryService
        from app.services.dependencies import get_category_service

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = get_category_service(repo=mock_repo, audit_service=mock_audit)

        assert isinstance(service, CategoryService)

    def test_get_export_service(self):
        from app.services.dependencies import get_export_service
        from app.services.export_service import ExportService

        mock_txn_svc = AsyncMock()
        service = get_export_service(transaction_service=mock_txn_svc)

        assert isinstance(service, ExportService)

    def test_get_reference_data_service(self):
        from app.services.dependencies import get_reference_data_service
        from app.services.reference_data_service import ReferenceDataService

        mock_acc = AsyncMock()
        mock_cat = AsyncMock()
        mock_tag = AsyncMock()
        service = get_reference_data_service(
            account_service=mock_acc,
            category_service=mock_cat,
            tag_service=mock_tag,
        )

        assert isinstance(service, ReferenceDataService)


# ---------------------------------------------------------------------------
# repositories/dependencies.py — module-level singleton getters
# ---------------------------------------------------------------------------


class TestRepositoriesDependencies:
    def test_get_transaction_repo(self):
        from app.repositories.cosmos.transaction_repo import CosmosTransactionRepository
        from app.repositories.dependencies import get_transaction_repo

        repo = get_transaction_repo()

        assert isinstance(repo, CosmosTransactionRepository)

    def test_get_reference_item_repo(self):
        from app.repositories.cosmos.reference_item_repo import CosmosReferenceItemRepository
        from app.repositories.dependencies import get_reference_item_repo

        repo = get_reference_item_repo()

        assert isinstance(repo, CosmosReferenceItemRepository)

    def test_get_category_repo(self):
        from app.repositories.cosmos.category_repo import CosmosCategoryRepository
        from app.repositories.dependencies import get_category_repo

        repo = get_category_repo()

        assert isinstance(repo, CosmosCategoryRepository)

    def test_get_audit_repo(self):
        from app.repositories.cosmos.audit_repo import CosmosAuditRepository
        from app.repositories.dependencies import get_audit_repo

        repo = get_audit_repo()

        assert isinstance(repo, CosmosAuditRepository)

    def test_repos_are_singletons(self):
        """Calling get_*_repo twice should return the same object."""
        from app.repositories.dependencies import get_transaction_repo

        assert get_transaction_repo() is get_transaction_repo()


# ---------------------------------------------------------------------------
# CosmosService
# ---------------------------------------------------------------------------


class TestCosmosService:
    async def test_initialize_with_key(self):
        """Test initialization with an explicit key (not Managed Identity)."""
        from app.services.cosmos_client import CosmosService

        svc = CosmosService.__new__(CosmosService)
        svc._client = None
        svc._database = None
        svc._containers = {}

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.get_database_client.return_value = mock_db
        mock_db.get_container_client.side_effect = lambda name: MagicMock(name=name)

        with patch("app.services.cosmos_client.CosmosClient", return_value=mock_client):
            await svc.initialize(
                endpoint="https://test.documents.azure.com:443/",
                database_name="test-db",
                key="test-key",
            )

        assert svc._client is mock_client
        assert "transactions" in svc._containers

    async def test_initialize_already_initialized_is_noop(self):
        """If _client is already set, initialize() should be a no-op."""
        from app.services.cosmos_client import CosmosService

        svc = CosmosService.__new__(CosmosService)
        existing_client = MagicMock()
        svc._client = existing_client
        svc._database = MagicMock()
        svc._containers = {}

        with patch("app.services.cosmos_client.CosmosClient") as mock_cls:
            await svc.initialize(endpoint="https://x.com", database_name="db", key="key")

        # CosmosClient constructor should NOT have been called again
        mock_cls.assert_not_called()
        assert svc._client is existing_client

    async def test_close(self):
        """Close should call client.close() and reset state."""
        from app.services.cosmos_client import CosmosService

        svc = CosmosService.__new__(CosmosService)
        mock_client = AsyncMock()
        svc._client = mock_client
        svc._database = MagicMock()
        svc._containers = {"transactions": MagicMock()}

        await svc.close()

        mock_client.close.assert_awaited_once()
        assert svc._client is None
        assert svc._containers == {}

    async def test_close_when_not_initialized(self):
        """Close when _client is None should be a no-op."""
        from app.services.cosmos_client import CosmosService

        svc = CosmosService.__new__(CosmosService)
        svc._client = None
        svc._database = None
        svc._containers = {}

        # Should not raise
        await svc.close()

    def test_container_properties(self):
        """Properties should return containers by name."""
        from app.services.cosmos_client import CosmosService

        svc = CosmosService.__new__(CosmosService)
        mock_txn = MagicMock(name="transactions")
        mock_cat = MagicMock(name="categories")
        mock_ref = MagicMock(name="reference_data")
        mock_audit = MagicMock(name="audit_log")
        svc._containers = {
            "transactions": mock_txn,
            "categories": mock_cat,
            "reference_data": mock_ref,
            "audit_log": mock_audit,
        }

        assert svc.transactions is mock_txn
        assert svc.categories is mock_cat
        assert svc.reference_data is mock_ref
        assert svc.audit_log is mock_audit
