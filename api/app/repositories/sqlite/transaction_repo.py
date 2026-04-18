"""SQLite skeleton for :class:`app.repositories.protocols.TransactionRepository`.

Phase A: methods raise :class:`NotImplementedError`. Phase B will implement
the SQL behind each method against the schema in
:mod:`app.repositories.sqlite.schema`.
"""

from __future__ import annotations

from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteTransactionRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    async def list_by_partition(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
        page_size: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        raise NotImplementedError("SqliteTransactionRepository.list_by_partition — Phase B")

    async def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
        raise NotImplementedError("SqliteTransactionRepository.get_by_id — Phase B")

    async def create(self, document: dict) -> dict:
        raise NotImplementedError("SqliteTransactionRepository.create — Phase B")

    async def replace(self, item_id: str, document: dict) -> dict:
        raise NotImplementedError("SqliteTransactionRepository.replace — Phase B")

    async def query_for_report(
        self,
        year: int,
        month: int | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError("SqliteTransactionRepository.query_for_report — Phase B")

    async def query_for_export(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError("SqliteTransactionRepository.query_for_export — Phase B")

    async def count_by_account(self, account_id: str) -> int:
        raise NotImplementedError("SqliteTransactionRepository.count_by_account — Phase B")

    async def count_by_category(self, category_id: str) -> int:
        raise NotImplementedError("SqliteTransactionRepository.count_by_category — Phase B")

    async def count_by_subcategory(self, category_id: str, subcategory_id: str) -> int:
        raise NotImplementedError("SqliteTransactionRepository.count_by_subcategory — Phase B")

    async def count_by_tag(self, tag_id: str) -> int:
        raise NotImplementedError("SqliteTransactionRepository.count_by_tag — Phase B")

    async def aggregate_filtered(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
    ) -> dict:
        raise NotImplementedError("SqliteTransactionRepository.aggregate_filtered — Phase B")
