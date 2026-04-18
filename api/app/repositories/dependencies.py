"""Backend-aware repository dependency injection.

Phase A of ``docs/specs/electron-sqlite-spec.md`` — see §4.1 (layering)
and §9 Phase A. The provider returns repository instances appropriate
for the configured ``DATA_BACKEND``:

* ``cosmos`` (default) — existing Cosmos-backed repositories. **No
  behavioral change** vs. before this refactor for cloud deployments.
* ``sqlite`` — Phase A skeletons (raise :class:`NotImplementedError`)
  that will be filled in during Phase B.

Returned types are the formal :mod:`app.repositories.protocols` protocols
so that callers (services, routers) cannot accidentally couple to a
concrete backend.
"""

from __future__ import annotations

from app.config import settings
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


def _build_repos() -> dict[str, object]:
    """Construct the singleton repository set for the configured backend."""
    backend = settings.DATA_BACKEND
    if backend == "sqlite":
        return {
            "transaction": SqliteTransactionRepository(),
            "reference_item": SqliteReferenceItemRepository(),
            "category": SqliteCategoryRepository(),
            "audit": SqliteAuditRepository(),
            "user_preferences": SqliteUserPreferencesRepository(),
        }
    # Default: cosmos. Any unknown value is rejected by the Settings
    # Literal type at startup, so this branch is the safe fallback.
    return {
        "transaction": CosmosTransactionRepository(),
        "reference_item": CosmosReferenceItemRepository(),
        "category": CosmosCategoryRepository(),
        "audit": CosmosAuditRepository(),
        "user_preferences": CosmosUserPreferencesRepository(),
    }


_repos: dict[str, object] = _build_repos()


def reset_repositories() -> None:
    """Rebuild the singleton repository set.

    Intended for tests that flip ``settings.DATA_BACKEND`` at runtime.
    Not used in production code paths.
    """
    global _repos
    _repos = _build_repos()


def get_transaction_repo() -> TransactionRepository:
    return _repos["transaction"]  # type: ignore[return-value]


def get_reference_item_repo() -> ReferenceItemRepository:
    return _repos["reference_item"]  # type: ignore[return-value]


def get_category_repo() -> CategoryRepository:
    return _repos["category"]  # type: ignore[return-value]


def get_audit_repo() -> AuditRepository:
    return _repos["audit"]  # type: ignore[return-value]


def get_user_preferences_repo() -> UserPreferencesRepository:
    return _repos["user_preferences"]  # type: ignore[return-value]
