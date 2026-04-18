"""SQLite implementation of :class:`app.repositories.protocols.AuditRepository`.

Append-only at the service layer (spec §8.4). Maps the canonical
Cosmos audit-entry document shape (camelCase) to the snake_case
``audit_log`` table per the Phase B B-1 mapping decision (2026-04-18).
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.repositories.sqlite._mapping import (
    dumps_json,
    loads_json,
    parse_iso,
    to_iso,
)
from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory

# Default trust tier for entries that arrive without an explicit
# ``actorSource`` (e.g. when running the cloud-side audit_service in
# desktop mode while Phase C identity work is still pending). Spec §6.5
# enumerates the four allowed values; ``entra_id`` is the cloud trust
# tier and is the safest default for pre-Phase-C entries.
_DEFAULT_ACTOR_SOURCE = "entra_id"


class SqliteAuditRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    # ------------------------------------------------------------------
    # Mapping helpers (single canonical pair per repo, per the B-1 decision).
    # ------------------------------------------------------------------
    @staticmethod
    def _from_doc(entry: dict) -> dict:
        """Convert a Cosmos-shaped audit document into row params for INSERT."""
        return {
            "id": entry["id"],
            "entity_type": entry.get("entityType"),
            "entity_id": entry.get("entityId"),
            "action": entry.get("action"),
            "changed_by": entry.get("changedBy"),
            "changed_by_name": entry.get("changedByName"),
            "changed_by_email": entry.get("changedByEmail"),
            "actor_source": entry.get("actorSource") or _DEFAULT_ACTOR_SOURCE,
            "changed_at": parse_iso(entry.get("changedAt")) or datetime.now(timezone.utc),
            "old_values": dumps_json(entry.get("oldValues")),
            "new_values": dumps_json(entry.get("newValues")),
            "metadata": dumps_json(entry.get("metadata")),
        }

    @staticmethod
    def _to_doc(row: Any) -> dict:
        """Convert a SQL row mapping into a Cosmos-shaped audit document."""
        return {
            "id": row["id"],
            "entityType": row["entity_type"],
            "entityId": row["entity_id"],
            "action": row["action"],
            "changedBy": row["changed_by"],
            "changedByName": row["changed_by_name"],
            "changedByEmail": row["changed_by_email"],
            "actorSource": row["actor_source"],
            "changedAt": to_iso(row["changed_at"]),
            "oldValues": loads_json(row["old_values"]) or {},
            "newValues": loads_json(row["new_values"]) or {},
            "metadata": loads_json(row["metadata"]),
        }

    # ------------------------------------------------------------------
    # Protocol methods
    # ------------------------------------------------------------------
    async def create(self, entry: dict) -> None:
        params = self._from_doc(entry)
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO audit_log "
                    "(id, entity_type, entity_id, action, changed_by, "
                    " changed_by_name, changed_by_email, actor_source, "
                    " changed_at, old_values, new_values, metadata) "
                    "VALUES (:id, :entity_type, :entity_id, :action, :changed_by, "
                    "        :changed_by_name, :changed_by_email, :actor_source, "
                    "        :changed_at, :old_values, :new_values, :metadata)"
                ),
                params,
            )

    async def query_trail(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page_size: int = 20,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        offset = _decode_offset(continuation_token)

        clauses: list[str] = []
        params: dict[str, Any] = {
            "limit": page_size,
            "offset": offset,
        }
        if entity_type:
            clauses.append("entity_type = :entity_type")
            params["entity_type"] = entity_type
        if entity_id:
            clauses.append("entity_id = :entity_id")
            params["entity_id"] = entity_id
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        query = (
            "SELECT id, entity_type, entity_id, action, changed_by, "
            "       changed_by_name, changed_by_email, actor_source, "
            "       changed_at, old_values, new_values, metadata "
            f"FROM audit_log{where} "
            "ORDER BY changed_at DESC "
            "LIMIT :limit OFFSET :offset"
        )

        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params)
            rows = result.mappings().all()

        items = [self._to_doc(r) for r in rows]
        next_token = _encode_offset(offset + len(items)) if len(items) == page_size else None
        return items, next_token


def _encode_offset(offset: int) -> str:
    """Opaque continuation token = base64-encoded JSON ``{"offset": N}``."""
    return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()


def _decode_offset(token: str | None) -> int:
    if not token:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        return int(payload.get("offset", 0))
    except (ValueError, KeyError, json.JSONDecodeError):
        return 0
