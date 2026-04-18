"""SQLite skeleton for :class:`app.repositories.protocols.ReferenceItemRepository`."""

from __future__ import annotations

from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteReferenceItemRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    async def list_all(self, item_type: str) -> list[dict]:
        raise NotImplementedError("SqliteReferenceItemRepository.list_all — Phase B")

    async def get_by_id(self, item_id: str, item_type: str) -> dict | None:
        raise NotImplementedError("SqliteReferenceItemRepository.get_by_id — Phase B")

    async def create(self, document: dict, item_type: str) -> dict:
        raise NotImplementedError("SqliteReferenceItemRepository.create — Phase B")

    async def replace(self, item_id: str, document: dict, item_type: str) -> dict:
        raise NotImplementedError("SqliteReferenceItemRepository.replace — Phase B")

    async def delete(self, item_id: str, item_type: str) -> None:
        raise NotImplementedError("SqliteReferenceItemRepository.delete — Phase B")
