"""Phase B parity tests — SqliteAuditRepository + SqliteUserPreferencesRepository.

These tests exercise the SQLite repos against an in-memory migrated SQLite
database (the ``sqlite_engine_factory`` fixture from
``tests.sqlite_fixtures``) and assert that the documents flowing in and
out match the canonical Cosmos document shape that services consume —
this is the "functional parity" gate from spec §4.3.1 and the Phase B
B-1 mapping decision (2026-04-18).

What "parity" means here, concretely:

* ``create``/``upsert`` accept the same camelCase document the Cosmos repo
  accepts today.
* ``query_trail``/``get`` return camelCase documents identical in shape to
  what services already consume from the Cosmos repo.
* The mapping layer is the *only* place the snake_case ↔ camelCase
  translation is allowed (spec §4.3.1 / B-1 decision).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

# Re-export the shared fixture so pytest discovers it from this module.
from tests.sqlite_fixtures import sqlite_engine_factory  # noqa: F401


def _audit_entry(**overrides) -> dict:
    base = {
        "id": f"au-{uuid4().hex[:8]}",
        "entityType": "Transaction",
        "entityId": "tx-001",
        "action": "Create",
        "changedBy": "user-oid-1",
        "changedByName": "Alice",
        "changedByEmail": "alice@example.org",
        "actorSource": "entra_id",
        "changedAt": "2026-04-18T12:00:00+00:00",
        "oldValues": {},
        "newValues": {"amount": "150.50", "transactionType": "income"},
    }
    base.update(overrides)
    return base


class TestSqliteAuditRepositoryParity:
    @pytest.fixture
    def repo(self, sqlite_engine_factory):
        from app.repositories.sqlite.audit_repo import SqliteAuditRepository

        return SqliteAuditRepository(engine_factory=sqlite_engine_factory)

    async def test_create_then_query_round_trips_document(self, repo):
        entry = _audit_entry()
        await repo.create(entry)

        items, token = await repo.query_trail(entity_type="Transaction", entity_id="tx-001")
        assert token is None
        assert len(items) == 1
        out = items[0]
        # Canonical Cosmos shape — no snake_case may leak through the mapping.
        for camel_key in (
            "id",
            "entityType",
            "entityId",
            "action",
            "changedBy",
            "changedByName",
            "changedByEmail",
            "actorSource",
            "changedAt",
            "oldValues",
            "newValues",
        ):
            assert camel_key in out, f"Missing canonical key {camel_key}: {out}"
        assert out["entityType"] == entry["entityType"]
        assert out["newValues"] == entry["newValues"]

    async def test_query_filters_by_entity_type(self, repo):
        await repo.create(_audit_entry(entityType="Transaction", entityId="tx-1"))
        await repo.create(_audit_entry(entityType="Category", entityId="cat-1"))

        items, _ = await repo.query_trail(entity_type="Category")
        assert len(items) == 1
        assert items[0]["entityType"] == "Category"

    async def test_query_filters_by_entity_id(self, repo):
        await repo.create(_audit_entry(entityId="tx-A"))
        await repo.create(_audit_entry(entityId="tx-B"))

        items, _ = await repo.query_trail(entity_id="tx-B")
        assert len(items) == 1
        assert items[0]["entityId"] == "tx-B"

    async def test_query_orders_by_changed_at_desc(self, repo):
        await repo.create(
            _audit_entry(id="au-1", changedAt="2026-01-01T00:00:00+00:00", entityId="tx-z")
        )
        await repo.create(
            _audit_entry(id="au-2", changedAt="2026-04-18T00:00:00+00:00", entityId="tx-z")
        )
        await repo.create(
            _audit_entry(id="au-3", changedAt="2026-02-15T00:00:00+00:00", entityId="tx-z")
        )

        items, _ = await repo.query_trail(entity_id="tx-z")
        assert [it["id"] for it in items] == ["au-2", "au-3", "au-1"]

    async def test_pagination_with_continuation_token(self, repo):
        for i in range(5):
            await repo.create(
                _audit_entry(
                    id=f"au-page-{i}",
                    changedAt=f"2026-04-{18 - i:02d}T00:00:00+00:00",
                    entityId="tx-page",
                )
            )

        page1, token1 = await repo.query_trail(entity_id="tx-page", page_size=2)
        assert len(page1) == 2
        assert token1 is not None

        page2, token2 = await repo.query_trail(
            entity_id="tx-page", page_size=2, continuation_token=token1
        )
        assert len(page2) == 2
        # No overlap.
        assert {it["id"] for it in page1}.isdisjoint({it["id"] for it in page2})

        page3, token3 = await repo.query_trail(
            entity_id="tx-page", page_size=2, continuation_token=token2
        )
        assert len(page3) == 1
        assert token3 is None  # Last page exhausts the result set.

    async def test_metadata_field_round_trips(self, repo):
        meta = {"reason": "manual fix", "by_request": "ops-ticket-42"}
        await repo.create(_audit_entry(id="au-meta", metadata=meta))

        items, _ = await repo.query_trail(entity_id="tx-001")
        assert items[0]["metadata"] == meta

    async def test_missing_actor_source_defaults_safely(self, repo):
        """Spec §6.5: actor_source is NOT NULL. Pre-Phase-C audit entries
        from the existing service may omit it; the SQLite repo must default
        rather than raising — see B-1 mapping decision."""
        entry = _audit_entry()
        entry.pop("actorSource")
        await repo.create(entry)

        items, _ = await repo.query_trail(entity_id="tx-001")
        assert items[0]["actorSource"] in {"entra_id", "os_username", "app_prompt", "microsoft_account"}

    async def test_returns_empty_list_when_no_match(self, repo):
        items, token = await repo.query_trail(entity_id="does-not-exist")
        assert items == []
        assert token is None


class TestSqliteUserPreferencesRepositoryParity:
    @pytest.fixture
    def repo(self, sqlite_engine_factory):
        from app.repositories.sqlite.user_preferences_repo import SqliteUserPreferencesRepository

        return SqliteUserPreferencesRepository(engine_factory=sqlite_engine_factory)

    async def test_get_unknown_user_returns_none(self, repo):
        result = await repo.get("never-seen")
        assert result is None

    async def test_upsert_then_get_round_trips(self, repo):
        prefs = {"theme": "dark", "currency": "EUR", "tableDensity": "compact"}
        out = await repo.upsert("user-1", prefs)
        # Cosmos parity: returned doc carries id + type + body.
        assert out["id"] == "user-1"
        assert out["type"] == "user_preferences"
        assert out["theme"] == "dark"
        assert out["currency"] == "EUR"
        assert out["tableDensity"] == "compact"

        fetched = await repo.get("user-1")
        assert fetched == out

    async def test_upsert_overwrites_existing_prefs(self, repo):
        await repo.upsert("user-2", {"theme": "light"})
        await repo.upsert("user-2", {"theme": "dark", "newField": 42})

        result = await repo.get("user-2")
        assert result["theme"] == "dark"
        assert result["newField"] == 42

    async def test_upsert_strips_id_and_type_from_body(self, repo):
        """`id` and `type` are reconstructed on read — they shouldn't
        leak into the persisted JSON body."""
        await repo.upsert("user-3", {"id": "should-be-ignored", "type": "wrong", "theme": "high-contrast"})
        out = await repo.get("user-3")
        assert out["id"] == "user-3"  # repo-managed, not from body
        assert out["type"] == "user_preferences"
        assert out["theme"] == "high-contrast"

    async def test_users_are_isolated(self, repo):
        await repo.upsert("user-a", {"locale": "es-ES"})
        await repo.upsert("user-b", {"locale": "en-US"})

        assert (await repo.get("user-a"))["locale"] == "es-ES"
        assert (await repo.get("user-b"))["locale"] == "en-US"
