"""SQLite skeleton for :class:`app.repositories.protocols.UserPreferencesRepository`."""

from __future__ import annotations

from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteUserPreferencesRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    async def get(self, user_oid: str) -> dict | None:
        raise NotImplementedError("SqliteUserPreferencesRepository.get — Phase B")

    async def upsert(self, user_oid: str, prefs: dict) -> dict:
        raise NotImplementedError("SqliteUserPreferencesRepository.upsert — Phase B")
