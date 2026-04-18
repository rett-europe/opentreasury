"""SQLite skeleton for :class:`app.repositories.protocols.AuditRepository`."""

from __future__ import annotations

from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteAuditRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    async def create(self, entry: dict) -> None:
        raise NotImplementedError("SqliteAuditRepository.create — Phase B")

    async def query_trail(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page_size: int = 20,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        raise NotImplementedError("SqliteAuditRepository.query_trail — Phase B")
