"""Tests for the Phase A SQLite schema and Alembic migration framework.

Covers (spec §4.3, §6.5, §9 Phase A):

* Initial migration applies cleanly to a fresh in-memory SQLite database.
* The resulting schema contains every table the spec requires, including
  ``app_identity`` and the reserved-empty ``users`` table.
* ``audit_log.actor_source`` exists and is constrained to the four
  trust-tier values from spec §6.5.
* Mutable tables expose ``updated_at`` and ``version`` columns for the
  optimistic-concurrency strategy planned in Phase D (spec §7.1).
* The reserved ``users`` table is empty after migration.
* The engine factory honors WAL mode and resolves paths sensibly.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.repositories.sqlite import schema
from app.repositories.sqlite.engine import (
    SqliteEngineFactory,
    _build_url,
    get_engine_factory,
    reset_engine_factory,
)
from app.repositories.sqlite.migrations.runner import (
    downgrade_to_base,
    upgrade_to_head,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_db_path(tmp_path: Path) -> str:
    """Return a path to a non-existent SQLite file in a temp dir."""
    return str(tmp_path / "phase_a.db")


def _table_names(db_path: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _columns(db_path: str, table: str) -> dict[str, dict]:
    conn = sqlite3.connect(db_path)
    try:
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {
            r[1]: {"type": r[2], "notnull": r[3], "default": r[4], "pk": r[5]}
            for r in rows
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration application
# ---------------------------------------------------------------------------


class TestMigrationsApplyCleanly:
    def test_upgrade_to_head_creates_all_expected_tables(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")

        actual = _table_names(fresh_db_path)
        # alembic_version is created by Alembic itself; expected_table_names
        # is the application schema only.
        actual.discard("alembic_version")

        expected = schema.expected_table_names()
        assert (
            actual == expected
        ), f"Schema drift. Missing: {expected - actual}. Extra: {actual - expected}"

    def test_required_tables_per_spec_exist(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")

        # Spec §4.3 enumerates these as required for Phase A.
        required = {
            "transactions",
            "categories",
            "reference_data",
            "audit_log",
            "app_identity",
            "users",  # reserved-empty per §4.3 / §6.4
            "user_preferences",
        }
        present = _table_names(fresh_db_path)
        assert required.issubset(
            present
        ), f"Missing required tables: {required - present}"

    def test_downgrade_to_base_drops_all_tables(self, fresh_db_path):
        url = f"sqlite:///{fresh_db_path}"
        upgrade_to_head(url)
        downgrade_to_base(url)

        present = _table_names(fresh_db_path)
        # Only Alembic's own bookkeeping table should remain.
        assert present <= {"alembic_version"}


# ---------------------------------------------------------------------------
# Spec-mandated columns
# ---------------------------------------------------------------------------


class TestActorSourceDiscriminator:
    """Spec §6.5 — actor_source column on audit_log."""

    def test_audit_log_has_actor_source(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        cols = _columns(fresh_db_path, "audit_log")
        assert "actor_source" in cols
        assert cols["actor_source"]["notnull"] == 1, "actor_source must be NOT NULL"

    def test_actor_source_check_constraint_rejects_unknown_values(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        conn = sqlite3.connect(fresh_db_path)
        # SQLite needs FK pragma echoed per-connection, but CHECK is always on.
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO audit_log "
                    "(id, entity_type, entity_id, action, changed_by, "
                    " actor_source, changed_at) "
                    "VALUES ('a1', 'Transaction', 'tx-1', 'Create', 'u1', "
                    "        'totally-bogus-source', '2026-04-18T00:00:00')"
                )
        finally:
            conn.close()

    @pytest.mark.parametrize(
        "actor_source",
        ["os_username", "app_prompt", "microsoft_account", "entra_id"],
    )
    def test_actor_source_accepts_each_documented_tier(
        self, fresh_db_path, actor_source
    ):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        conn = sqlite3.connect(fresh_db_path)
        try:
            conn.execute(
                "INSERT INTO audit_log "
                "(id, entity_type, entity_id, action, changed_by, "
                " actor_source, changed_at) "
                "VALUES (?, 'Transaction', 'tx-1', 'Create', 'u1', ?, "
                "        '2026-04-18T00:00:00')",
                (f"audit-{actor_source}", actor_source),
            )
            conn.commit()
        finally:
            conn.close()


class TestOptimisticConcurrencyColumns:
    """Spec §7.1 / §9 — updated_at + version on mutable tables for Phase D."""

    @pytest.mark.parametrize(
        "table",
        ["transactions", "categories", "reference_data", "user_preferences"],
    )
    def test_table_has_version_and_updated_at(self, fresh_db_path, table):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        cols = _columns(fresh_db_path, table)
        assert "version" in cols, f"{table} missing version column"
        assert "updated_at" in cols, f"{table} missing updated_at column"


class TestSoftDeleteColumns:
    """Spec §4.3 — soft-delete invariant must be representable in SQLite."""

    @pytest.mark.parametrize(
        "table",
        ["transactions", "categories", "reference_data"],
    )
    def test_table_has_soft_delete_columns(self, fresh_db_path, table):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        cols = _columns(fresh_db_path, table)
        assert "is_deleted" in cols
        assert "deleted_at" in cols


class TestReservedUsersTable:
    """Spec §4.3 / §6.4 — users table exists but is empty in Phase A."""

    def test_users_table_is_present_and_empty(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        conn = sqlite3.connect(fresh_db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        finally:
            conn.close()
        assert count == 0


class TestAppIdentityTable:
    """Spec §4.3 / §6.2 — app_identity stores the local user's display name."""

    def test_app_identity_columns(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        cols = _columns(fresh_db_path, "app_identity")
        for required in ("id", "display_name", "actor_source", "created_at"):
            assert required in cols, f"app_identity missing {required}"
        assert cols["display_name"]["notnull"] == 1
        assert cols["actor_source"]["notnull"] == 1


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------


class TestEngineFactory:
    def test_build_url_for_memory_db(self):
        assert _build_url(":memory:") == "sqlite+aiosqlite:///:memory:"

    def test_build_url_for_filesystem_path_is_absolute(self, tmp_path):
        rel = "some.db"
        url = _build_url(rel)
        assert url.startswith("sqlite+aiosqlite:///")
        # Must have been resolved to absolute, not left as the relative input.
        path_part = url.removeprefix("sqlite+aiosqlite:///")
        assert Path(path_part).is_absolute()

    def test_get_engine_factory_returns_singleton(self):
        a = get_engine_factory()
        b = get_engine_factory()
        assert a is b

    def test_reset_engine_factory_replaces_singleton(self):
        original = get_engine_factory()
        replacement = reset_engine_factory(db_path=":memory:")
        assert replacement is not original
        assert replacement.db_path == ":memory:"
        # Restore default for downstream tests.
        reset_engine_factory()

    @pytest.mark.asyncio
    async def test_engine_pragmas_apply_wal_mode(self, tmp_path):
        # Build a real file-backed engine (in-memory SQLite cannot use WAL).
        db_path = tmp_path / "wal-test.db"
        factory = SqliteEngineFactory(db_path=str(db_path))
        engine = factory.get_engine()

        from sqlalchemy import text

        async with engine.connect() as conn:
            mode = (await conn.execute(text("PRAGMA journal_mode"))).scalar_one()
            fk = (await conn.execute(text("PRAGMA foreign_keys"))).scalar_one()

        await factory.dispose()

        assert mode.lower() == "wal", f"Expected WAL journal mode, got {mode!r}"
        assert int(fk) == 1, "foreign_keys pragma must be ON"


# ---------------------------------------------------------------------------
# Idempotency / repeated upgrade safety (defends future Phase B work)
# ---------------------------------------------------------------------------


class TestRepeatedUpgradeIsSafe:
    def test_running_upgrade_twice_does_not_error(self, fresh_db_path):
        url = f"sqlite:///{fresh_db_path}"
        upgrade_to_head(url)
        # Second call should be a no-op — Alembic recognizes head.
        upgrade_to_head(url)


# ---------------------------------------------------------------------------
# Sanity: an actual record can be written into every table after migration.
# This is the proof that the schema isn't just structurally present but
# also coherent (NOT NULLs and CHECKs aren't contradicting the doc shape).
# ---------------------------------------------------------------------------


class TestSchemaIsWritable:
    def test_can_insert_minimal_row_into_every_table(self, fresh_db_path):
        upgrade_to_head(f"sqlite:///{fresh_db_path}")
        conn = sqlite3.connect(fresh_db_path)
        ts = "2026-04-18T12:00:00"
        try:
            conn.execute(
                "INSERT INTO reference_data (id, type, name, created_at) "
                "VALUES ('acc-1', 'account', 'Main Account', ?)",
                (ts,),
            )
            conn.execute(
                "INSERT INTO categories (id, name, category_type, created_at) "
                "VALUES ('cat-1', 'Donations', 'income', ?)",
                (ts,),
            )
            conn.execute(
                "INSERT INTO transactions "
                "(id, partition_key, date, year, month, amount, "
                " transaction_type, created_by, created_at) "
                "VALUES ('tx-1', 'tx-acc-1', '2026-04-18', 2026, 4, 150.50, "
                "        'income', 'u1', ?)",
                (ts,),
            )
            conn.execute(
                "INSERT INTO audit_log "
                "(id, entity_type, entity_id, action, changed_by, "
                " actor_source, changed_at) "
                "VALUES ('au-1', 'Transaction', 'tx-1', 'Create', 'u1', "
                "        'os_username', ?)",
                (ts,),
            )
            conn.execute(
                "INSERT INTO app_identity "
                "(id, display_name, actor_source, created_at) "
                "VALUES ('id-1', 'Alice', 'app_prompt', ?)",
                (ts,),
            )
            conn.execute(
                "INSERT INTO user_preferences (user_oid, preferences) "
                "VALUES ('u1', '{}')",
            )
            conn.commit()
        finally:
            conn.close()
