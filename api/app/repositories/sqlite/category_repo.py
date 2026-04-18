"""SQLite implementation of :class:`app.repositories.protocols.CategoryRepository`.

Maps the canonical Cosmos category-document shape (camelCase) to the
snake_case ``categories`` table per the Phase B B-1 mapping decision
(2026-04-18). Subcategories are stored as an embedded JSON array, mirroring
the Cosmos document.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.repositories.sqlite._mapping import (
    bool_from_int,
    dumps_json,
    loads_json,
    parse_iso,
    to_iso,
)
from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


class SqliteCategoryRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    # ------------------------------------------------------------------
    # Mapping helpers (B-1 decision: one canonical pair per repo).
    # ------------------------------------------------------------------
    @staticmethod
    def _to_doc(row: Any) -> dict:
        return {
            "id": row["id"],
            "type": "category",
            "name": row["name"],
            "description": row["description"],
            "categoryType": row["category_type"],
            "sortOrder": row["sort_order"],
            "subcategories": loads_json(row["subcategories"]) or [],
            "createdBy": row["created_by"],
            "createdAt": to_iso(row["created_at"]),
            "updatedBy": row["updated_by"],
            "updatedAt": to_iso(row["updated_at"]),
            "version": row["version"],
            "isDeleted": bool_from_int(row["is_deleted"]),
            "deletedAt": to_iso(row["deleted_at"]),
        }

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        return {
            "id": doc["id"],
            "name": doc.get("name"),
            "description": doc.get("description"),
            "category_type": doc.get("categoryType"),
            "sort_order": doc.get("sortOrder"),
            "subcategories": dumps_json(doc.get("subcategories") or []),
            "created_by": doc.get("createdBy"),
            "created_at": parse_iso(doc.get("createdAt")) or datetime.now(timezone.utc),
            "updated_by": doc.get("updatedBy"),
            "updated_at": parse_iso(doc.get("updatedAt")),
            "is_deleted": 1 if doc.get("isDeleted") else 0,
            "deleted_at": parse_iso(doc.get("deletedAt")),
        }

    # ------------------------------------------------------------------
    # Protocol methods
    # ------------------------------------------------------------------
    async def list_all(self) -> list[dict]:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM categories " "WHERE is_deleted = 0 " "ORDER BY sort_order ASC, name ASC")
            )
            return [self._to_doc(row) for row in result.mappings()]

    async def get_by_id(self, category_id: str) -> dict | None:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM categories WHERE id = :id AND is_deleted = 0"),
                {"id": category_id},
            )
            row = result.mappings().first()
        if row is None:
            return None
        return self._to_doc(row)

    async def create(self, document: dict) -> dict:
        params = self._from_doc(document)
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO categories "
                    "(id, name, description, category_type, sort_order, "
                    " subcategories, created_by, created_at, updated_by, "
                    " updated_at, is_deleted, deleted_at) "
                    "VALUES (:id, :name, :description, :category_type, :sort_order, "
                    "        :subcategories, :created_by, :created_at, :updated_by, "
                    "        :updated_at, :is_deleted, :deleted_at)"
                ),
                params,
            )
        return await self.get_by_id(document["id"])  # type: ignore[return-value]

    async def replace(self, category_id: str, document: dict) -> dict:
        # Cosmos parity: ``replace_item`` overwrites the whole document.
        params = self._from_doc({**document, "id": category_id})
        # version is bumped on every replace (Phase D will use this for OCC).
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE categories SET "
                    "    name = :name, "
                    "    description = :description, "
                    "    category_type = :category_type, "
                    "    sort_order = :sort_order, "
                    "    subcategories = :subcategories, "
                    "    updated_by = :updated_by, "
                    "    updated_at = :updated_at, "
                    "    is_deleted = :is_deleted, "
                    "    deleted_at = :deleted_at, "
                    "    version = version + 1 "
                    "WHERE id = :id"
                ),
                params,
            )
        result = await self.get_by_id(category_id)
        if result is None:
            # ``replace`` of a soft-deleted row leaves it filtered from get_by_id
            # — fall back to a raw fetch so the caller still sees the persisted
            # state (matches Cosmos's ``replace_item`` returning the doc).
            engine2 = self._engine_factory.get_engine()
            async with engine2.connect() as conn:
                row = (
                    (
                        await conn.execute(
                            text("SELECT * FROM categories WHERE id = :id"),
                            {"id": category_id},
                        )
                    )
                    .mappings()
                    .first()
                )
            if row is None:
                # Cosmos would raise here; mirror with a KeyError-equivalent.
                raise KeyError(f"category {category_id!r} not found")
            return self._to_doc(row)
        return result

    async def delete(self, category_id: str) -> None:
        # Cosmos's ``delete_item`` is hard-delete; we mirror that semantically.
        # Soft-delete is the *service*'s responsibility (it flips ``isDeleted``
        # via ``replace``); ``delete`` is reserved for cleanup paths.
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM categories WHERE id = :id"),
                {"id": category_id},
            )
