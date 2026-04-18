"""SQLite implementation of :class:`app.repositories.protocols.UserPreferencesRepository`.

The Cosmos backend stores preferences in the shared ``reference_data``
container with ``type=user_preferences``, so the Cosmos-shaped document
returned by ``upsert``/``get`` always carries ``id`` and ``type`` fields
alongside the actual preference body. SQLite uses a dedicated
``user_preferences`` table whose ``preferences`` JSON column holds the
body verbatim; the repo re-assembles the full document on read so
service callers see the same shape regardless of backend (B-1 mapping
decision, 2026-04-18).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.repositories.sqlite._mapping import dumps_json, loads_json
from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory

_PREFERENCES_TYPE = "user_preferences"


class SqliteUserPreferencesRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    @staticmethod
    def _to_doc(user_oid: str, prefs_blob: Any) -> dict:
        body = loads_json(prefs_blob) or {}
        # Re-emit in the Cosmos document shape: id + type + preference fields.
        return {
            "id": user_oid,
            "type": _PREFERENCES_TYPE,
            **body,
        }

    @staticmethod
    def _from_doc(prefs: dict) -> dict:
        # Strip the housekeeping keys so the JSON body stores only the
        # actual preferences (id/type are reconstructed on read).
        return {k: v for k, v in prefs.items() if k not in {"id", "type"}}

    async def get(self, user_oid: str) -> dict | None:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT preferences FROM user_preferences WHERE user_oid = :oid"),
                {"oid": user_oid},
            )
            row = result.mappings().first()
        if row is None:
            return None
        return self._to_doc(user_oid, row["preferences"])

    async def upsert(self, user_oid: str, prefs: dict) -> dict:
        body = self._from_doc(prefs)
        body_json = dumps_json(body) or "{}"
        now = datetime.now(timezone.utc)
        engine = self._engine_factory.get_engine()
        # SQLite supports ``INSERT ... ON CONFLICT`` which gives us native
        # upsert semantics matching Cosmos's ``upsert_item`` behavior.
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO user_preferences (user_oid, preferences, updated_at, version) "
                    "VALUES (:oid, :prefs, :updated_at, 1) "
                    "ON CONFLICT(user_oid) DO UPDATE SET "
                    "    preferences = excluded.preferences, "
                    "    updated_at = excluded.updated_at, "
                    "    version = user_preferences.version + 1"
                ),
                {"oid": user_oid, "prefs": body_json, "updated_at": now},
            )
        return self._to_doc(user_oid, body_json)
