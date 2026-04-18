"""SQLite repository implementations for OpenTreasury desktop mode.

Phase A skeletons of the SQLite-backed repositories (see
``docs/specs/electron-sqlite-spec.md`` §4 and §9 Phase A). Classes implement
the protocols in ``app.repositories.protocols`` so the dependency-injection
provider can swap them in for the Cosmos implementations when
``DATA_BACKEND=sqlite``.

In Phase A every method raises :class:`NotImplementedError`. Phase B will
replace these stubs with real SQL-backed logic against the schema defined
in ``app.repositories.sqlite.schema``.
"""

from app.repositories.sqlite.audit_repo import SqliteAuditRepository
from app.repositories.sqlite.category_repo import SqliteCategoryRepository
from app.repositories.sqlite.engine import (
    SqliteEngineFactory,
    get_engine_factory,
    reset_engine_factory,
)
from app.repositories.sqlite.reference_item_repo import SqliteReferenceItemRepository
from app.repositories.sqlite.transaction_repo import SqliteTransactionRepository
from app.repositories.sqlite.user_preferences_repo import (
    SqliteUserPreferencesRepository,
)

__all__ = [
    "SqliteAuditRepository",
    "SqliteCategoryRepository",
    "SqliteEngineFactory",
    "SqliteReferenceItemRepository",
    "SqliteTransactionRepository",
    "SqliteUserPreferencesRepository",
    "get_engine_factory",
    "reset_engine_factory",
]
