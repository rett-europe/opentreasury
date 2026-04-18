"""SQLite implementation of :class:`app.repositories.protocols.ReferenceItemRepository`.

The Cosmos backend stores accounts, tags, and other lookup items in a
single ``reference_data`` container partitioned by ``type``. SQLite uses
the same single-table-with-discriminator shape (``reference_data`` table
with a ``type`` column) so the repo protocol is satisfiable identically
on both backends. Mapping between snake_case columns and camelCase doc
fields lives in the ``_to_doc`` / ``_from_doc`` helpers below per the
B-1 mapping decision (2026-04-18).
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


class SqliteReferenceItemRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    @staticmethod
    def _to_doc(row: Any) -> dict:
        # Reference-item docs are flat: most type-specific fields are in
        # the ``attributes`` JSON bag, but we hoist them up to top-level
        # keys to match the Cosmos document shape that callers see today.
        attributes = loads_json(row["attributes"]) or {}
        doc = {
            "id": row["id"],
            "type": row["type"],
            "name": row["name"],
            "description": row["description"],
            "sortOrder": row["sort_order"],
            "createdBy": row["created_by"],
            "createdAt": to_iso(row["created_at"]),
            "updatedBy": row["updated_by"],
            "updatedAt": to_iso(row["updated_at"]),
            "version": row["version"],
            "isDeleted": bool_from_int(row["is_deleted"]),
            "deletedAt": to_iso(row["deleted_at"]),
        }
        # Type-specific fields (currency for accounts, color for tags, …)
        # live alongside the canonical ones at the top level.
        for k, v in attributes.items():
            doc.setdefault(k, v)
        return doc

    @staticmethod
    def _from_doc(doc: dict, item_type: str) -> dict:
        # Strip canonical keys; everything else becomes the attributes bag.
        canonical = {
            "id",
            "type",
            "name",
            "description",
            "sortOrder",
            "createdBy",
            "createdAt",
            "updatedBy",
            "updatedAt",
            "version",
            "isDeleted",
            "deletedAt",
        }
        attributes = {k: v for k, v in doc.items() if k not in canonical}
        return {
            "id": doc["id"],
            "type": item_type,
            "name": doc.get("name"),
            "description": doc.get("description"),
            "sort_order": doc.get("sortOrder"),
            "attributes": dumps_json(attributes) if attributes else None,
            "created_by": doc.get("createdBy"),
            "created_at": parse_iso(doc.get("createdAt")) or datetime.now(timezone.utc),
            "updated_by": doc.get("updatedBy"),
            "updated_at": parse_iso(doc.get("updatedAt")),
            "is_deleted": 1 if doc.get("isDeleted") else 0,
            "deleted_at": parse_iso(doc.get("deletedAt")),
        }

    async def list_all(self, item_type: str) -> list[dict]:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT * FROM reference_data "
                    "WHERE type = :type AND is_deleted = 0 "
                    "ORDER BY sort_order ASC, name ASC"
                ),
                {"type": item_type},
            )
            return [self._to_doc(row) for row in result.mappings()]

    async def get_by_id(self, item_id: str, item_type: str) -> dict | None:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM reference_data " "WHERE id = :id AND type = :type AND is_deleted = 0"),
                {"id": item_id, "type": item_type},
            )
            row = result.mappings().first()
        if row is None:
            return None
        return self._to_doc(row)

    async def create(self, document: dict, item_type: str) -> dict:
        params = self._from_doc(document, item_type)
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO reference_data "
                    "(id, type, name, description, sort_order, attributes, "
                    " created_by, created_at, updated_by, updated_at, "
                    " is_deleted, deleted_at) "
                    "VALUES (:id, :type, :name, :description, :sort_order, :attributes, "
                    "        :created_by, :created_at, :updated_by, :updated_at, "
                    "        :is_deleted, :deleted_at)"
                ),
                params,
            )
        return await self.get_by_id(document["id"], item_type)  # type: ignore[return-value]

    async def replace(self, item_id: str, document: dict, item_type: str) -> dict:
        params = self._from_doc({**document, "id": item_id}, item_type)
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE reference_data SET "
                    "    name = :name, "
                    "    description = :description, "
                    "    sort_order = :sort_order, "
                    "    attributes = :attributes, "
                    "    updated_by = :updated_by, "
                    "    updated_at = :updated_at, "
                    "    is_deleted = :is_deleted, "
                    "    deleted_at = :deleted_at, "
                    "    version = version + 1 "
                    "WHERE id = :id AND type = :type"
                ),
                params,
            )
        result = await self.get_by_id(item_id, item_type)
        if result is None:
            engine2 = self._engine_factory.get_engine()
            async with engine2.connect() as conn:
                row = (
                    (
                        await conn.execute(
                            text("SELECT * FROM reference_data " "WHERE id = :id AND type = :type"),
                            {"id": item_id, "type": item_type},
                        )
                    )
                    .mappings()
                    .first()
                )
            if row is None:
                raise KeyError(f"reference_data item {item_id!r} of type {item_type!r} not found")
            return self._to_doc(row)
        return result

    async def delete(self, item_id: str, item_type: str) -> None:
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM reference_data " "WHERE id = :id AND type = :type"),
                {"id": item_id, "type": item_type},
            )
