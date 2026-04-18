from __future__ import annotations

from typing import Protocol


class TransactionRepository(Protocol):
    async def list_by_partition(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
        page_size: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]: ...

    async def get_by_id(self, item_id: str, partition_key: str) -> dict | None: ...

    async def create(self, document: dict) -> dict: ...

    async def replace(self, item_id: str, document: dict) -> dict: ...

    async def query_for_report(
        self,
        year: int,
        month: int | None = None,
        account_id: str | None = None,
    ) -> list[dict]: ...

    async def query_for_export(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict]: ...

    async def count_by_account(self, account_id: str) -> int: ...

    async def count_by_category(self, category_id: str) -> int: ...

    async def count_by_subcategory(self, category_id: str, subcategory_id: str) -> int: ...

    async def count_by_tag(self, tag_id: str) -> int: ...

    async def aggregate_filtered(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
    ) -> dict: ...


class ReferenceItemRepository(Protocol):
    """Shared protocol for accounts, tags, and other reference_data items."""

    async def list_all(self, item_type: str) -> list[dict]: ...

    async def get_by_id(self, item_id: str, item_type: str) -> dict | None: ...

    async def create(self, document: dict, item_type: str) -> dict: ...

    async def replace(self, item_id: str, document: dict, item_type: str) -> dict: ...

    async def delete(self, item_id: str, item_type: str) -> None: ...


class CategoryRepository(Protocol):
    async def list_all(self) -> list[dict]: ...

    async def get_by_id(self, category_id: str) -> dict | None: ...

    async def create(self, document: dict) -> dict: ...

    async def replace(self, category_id: str, document: dict) -> dict: ...

    async def delete(self, category_id: str) -> None: ...


class AuditRepository(Protocol):
    async def create(self, entry: dict) -> None: ...

    async def query_trail(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page_size: int = 20,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]: ...


class UserPreferencesRepository(Protocol):
    async def get(self, user_oid: str) -> dict | None: ...

    async def upsert(self, user_oid: str, prefs: dict) -> dict: ...
