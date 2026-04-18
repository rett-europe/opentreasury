"""SQLite async engine factory for desktop mode.

Phase A scope (per ``docs/specs/electron-sqlite-spec.md`` §9 Phase A and
§7.1): produce an ``aiosqlite``-backed SQLAlchemy engine for the configured
database file, with WAL mode honored from the start. The engine factory is
the only place that knows how to build a connection — repositories take it
via DI rather than constructing connections themselves.

Locking / advisory-lock-file behavior (``.opentreasury.lock``) is **not**
implemented here — that's Phase D (spec §7.1). Phase A provides only the
plumbing required for the Phase A migrations and Phase B repositories.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


def _build_url(db_path: str) -> str:
    """Return the SQLAlchemy URL for the configured SQLite database file.

    The special value ``":memory:"`` is preserved as an in-memory database,
    which is used by tests. All other paths are treated as filesystem paths
    (created on first connect by SQLite itself).
    """
    if db_path == ":memory:":
        return "sqlite+aiosqlite:///:memory:"
    # Resolve to an absolute path so behavior doesn't depend on CWD.
    absolute = str(Path(db_path).expanduser().resolve())
    return f"sqlite+aiosqlite:///{absolute}"


def _apply_pragmas(dbapi_connection, _connection_record) -> None:
    """Apply per-connection PRAGMAs.

    * ``journal_mode=WAL`` is mandated by spec §7.1 for Team mode safety,
      and it is the right default for Local mode too (better crash recovery).
    * ``foreign_keys=ON`` matches the SQLAlchemy idiom for SQLite — without
      it, FK constraints declared in the schema would not be enforced.
    * ``synchronous=NORMAL`` is the recommended pairing with WAL: durable
      across application crashes, faster than FULL, and acceptable for
      OpenTreasury's small-team write volume.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


class SqliteEngineFactory:
    """Builds and caches the SQLite ``AsyncEngine``.

    Single instance per process. Reset via :func:`reset_engine_factory`
    when tests need to swap configurations.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.SQLITE_DB_PATH
        self._engine: AsyncEngine | None = None

    @property
    def db_path(self) -> str:
        return self._db_path

    @property
    def url(self) -> str:
        return _build_url(self._db_path)

    def get_engine(self) -> AsyncEngine:
        """Return a process-wide cached :class:`AsyncEngine`."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> AsyncEngine:
        engine = create_async_engine(
            self.url,
            future=True,
            # Echo is intentionally off; the desktop runtime should be quiet
            # by default. Tests / debug builds can wrap their own engine.
            echo=False,
        )
        # Hook PRAGMAs onto the underlying sync DBAPI connection. The
        # async engine wraps a sync engine; ``sync_engine`` exposes it.
        event.listen(engine.sync_engine, "connect", _apply_pragmas)
        return engine

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None


_factory: SqliteEngineFactory | None = None


def get_engine_factory() -> SqliteEngineFactory:
    """Return the process-wide :class:`SqliteEngineFactory`."""
    global _factory
    if _factory is None:
        _factory = SqliteEngineFactory()
    return _factory


def reset_engine_factory(db_path: str | None = None) -> SqliteEngineFactory:
    """Replace the cached factory. Intended for tests and migrations.

    If ``db_path`` is provided, the new factory uses that path; otherwise
    the value from :data:`settings` is used.
    """
    global _factory
    _factory = SqliteEngineFactory(db_path=db_path)
    return _factory


__all__ = [
    "SqliteEngineFactory",
    "get_engine_factory",
    "reset_engine_factory",
]
