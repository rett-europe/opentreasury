"""SQLite skeleton for :class:`app.repositories.protocols.CategoryRepository`."""

from __future__ import annotations

from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteCategoryRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    async def list_all(self) -> list[dict]:
        raise NotImplementedError("SqliteCategoryRepository.list_all — Phase B")

    async def get_by_id(self, category_id: str) -> dict | None:
        raise NotImplementedError("SqliteCategoryRepository.get_by_id — Phase B")

    async def create(self, document: dict) -> dict:
        raise NotImplementedError("SqliteCategoryRepository.create — Phase B")

    async def replace(self, category_id: str, document: dict) -> dict:
        raise NotImplementedError("SqliteCategoryRepository.replace — Phase B")

    async def delete(self, category_id: str) -> None:
        raise NotImplementedError("SqliteCategoryRepository.delete — Phase B")
