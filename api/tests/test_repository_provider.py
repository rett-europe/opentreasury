"""Tests for the Phase A backend selector (Electron + SQLite spec §4, §9 Phase A).

Covers:

* Default ``DATA_BACKEND=cosmos`` returns Cosmos-backed repositories
  (existing-deployment behavior is unchanged).
* ``DATA_BACKEND=sqlite`` returns the SQLite skeleton repositories.
* All concrete repositories — Cosmos and SQLite — are structurally
  compatible with the Protocols declared in
  :mod:`app.repositories.protocols`.
* The provider returns a stable singleton between calls.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.repositories import dependencies as deps
from app.repositories.cosmos.audit_repo import CosmosAuditRepository
from app.repositories.cosmos.category_repo import CosmosCategoryRepository
from app.repositories.cosmos.reference_item_repo import CosmosReferenceItemRepository
from app.repositories.cosmos.transaction_repo import CosmosTransactionRepository
from app.repositories.cosmos.user_preferences_repo import (
    CosmosUserPreferencesRepository,
)
from app.repositories.protocols import (
    AuditRepository,
    CategoryRepository,
    ReferenceItemRepository,
    TransactionRepository,
    UserPreferencesRepository,
)
from app.repositories.sqlite.audit_repo import SqliteAuditRepository
from app.repositories.sqlite.category_repo import SqliteCategoryRepository
from app.repositories.sqlite.reference_item_repo import SqliteReferenceItemRepository
from app.repositories.sqlite.transaction_repo import SqliteTransactionRepository
from app.repositories.sqlite.user_preferences_repo import (
    SqliteUserPreferencesRepository,
)


@pytest.fixture
def restore_backend():
    """Restore DATA_BACKEND and the singleton repo set after a test mutates them."""
    original = settings.DATA_BACKEND
    yield
    settings.DATA_BACKEND = original
    deps.reset_repositories()


class TestDefaultBackendIsCosmos:
    def test_default_setting_is_cosmos(self):
        # The spec mandates that existing deployments see no behavioral
        # change after Phase A merges — the default must remain `cosmos`.
        assert settings.DATA_BACKEND == "cosmos"

    def test_provider_returns_cosmos_repos_by_default(self):
        assert isinstance(deps.get_transaction_repo(), CosmosTransactionRepository)
        assert isinstance(deps.get_reference_item_repo(), CosmosReferenceItemRepository)
        assert isinstance(deps.get_category_repo(), CosmosCategoryRepository)
        assert isinstance(deps.get_audit_repo(), CosmosAuditRepository)
        assert isinstance(
            deps.get_user_preferences_repo(), CosmosUserPreferencesRepository
        )


class TestSqliteBackendSelection:
    def test_provider_returns_sqlite_repos_when_configured(self, restore_backend):
        settings.DATA_BACKEND = "sqlite"
        deps.reset_repositories()

        assert isinstance(deps.get_transaction_repo(), SqliteTransactionRepository)
        assert isinstance(deps.get_reference_item_repo(), SqliteReferenceItemRepository)
        assert isinstance(deps.get_category_repo(), SqliteCategoryRepository)
        assert isinstance(deps.get_audit_repo(), SqliteAuditRepository)
        assert isinstance(
            deps.get_user_preferences_repo(), SqliteUserPreferencesRepository
        )


class TestSingletonStability:
    def test_repeated_calls_return_same_instance(self):
        assert deps.get_transaction_repo() is deps.get_transaction_repo()
        assert deps.get_audit_repo() is deps.get_audit_repo()
        assert deps.get_user_preferences_repo() is deps.get_user_preferences_repo()


class TestProtocolConformance:
    """Structural-typing check: both backends must satisfy the protocols.

    ``isinstance`` works on :class:`typing.Protocol` only when the
    protocol is decorated ``@runtime_checkable``. The protocols in this
    project are not, so we instead verify each method signature exists
    and is a coroutine function — the contract that callers rely on.
    """

    @staticmethod
    def _assert_implements(instance, protocol_cls) -> None:
        from inspect import iscoroutinefunction

        for name, member in vars(protocol_cls).items():
            if name.startswith("_") or not callable(member):
                continue
            attr = getattr(instance, name, None)
            assert (
                attr is not None
            ), f"{instance.__class__.__name__} missing method {name}"
            assert iscoroutinefunction(attr), (
                f"{instance.__class__.__name__}.{name} must be async to satisfy "
                f"{protocol_cls.__name__}"
            )

    def test_cosmos_transaction_repo_satisfies_protocol(self):
        self._assert_implements(CosmosTransactionRepository(), TransactionRepository)

    def test_sqlite_transaction_repo_satisfies_protocol(self):
        self._assert_implements(SqliteTransactionRepository(), TransactionRepository)

    def test_cosmos_category_repo_satisfies_protocol(self):
        self._assert_implements(CosmosCategoryRepository(), CategoryRepository)

    def test_sqlite_category_repo_satisfies_protocol(self):
        self._assert_implements(SqliteCategoryRepository(), CategoryRepository)

    def test_cosmos_reference_item_repo_satisfies_protocol(self):
        self._assert_implements(
            CosmosReferenceItemRepository(), ReferenceItemRepository
        )

    def test_sqlite_reference_item_repo_satisfies_protocol(self):
        self._assert_implements(
            SqliteReferenceItemRepository(), ReferenceItemRepository
        )

    def test_cosmos_audit_repo_satisfies_protocol(self):
        self._assert_implements(CosmosAuditRepository(), AuditRepository)

    def test_sqlite_audit_repo_satisfies_protocol(self):
        self._assert_implements(SqliteAuditRepository(), AuditRepository)

    def test_cosmos_user_preferences_repo_satisfies_protocol(self):
        self._assert_implements(
            CosmosUserPreferencesRepository(), UserPreferencesRepository
        )

    def test_sqlite_user_preferences_repo_satisfies_protocol(self):
        self._assert_implements(
            SqliteUserPreferencesRepository(), UserPreferencesRepository
        )


class TestSqliteSkeletonsRaiseNotImplemented:
    """Phase A skeletons must raise NotImplementedError, not silently no-op."""

    @pytest.mark.asyncio
    async def test_transaction_methods_raise(self):
        repo = SqliteTransactionRepository()
        with pytest.raises(NotImplementedError):
            await repo.get_by_id("x", "pk")
        with pytest.raises(NotImplementedError):
            await repo.create({})

    @pytest.mark.asyncio
    async def test_category_methods_raise(self):
        repo = SqliteCategoryRepository()
        with pytest.raises(NotImplementedError):
            await repo.list_all()

    @pytest.mark.asyncio
    async def test_audit_methods_raise(self):
        repo = SqliteAuditRepository()
        with pytest.raises(NotImplementedError):
            await repo.create({})

    @pytest.mark.asyncio
    async def test_user_preferences_methods_raise(self):
        repo = SqliteUserPreferencesRepository()
        with pytest.raises(NotImplementedError):
            await repo.get("oid")
