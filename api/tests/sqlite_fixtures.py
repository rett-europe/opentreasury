"""Shared SQLite test infrastructure for Phase B parity tests.

Provides a single fixture, :func:`sqlite_engine_factory`, that hands every
parity test an isolated, migrated, in-memory SQLite database wrapped in a
:class:`SqliteEngineFactory`. Each fixture invocation:

1. Allocates a tempfile-backed SQLite database (in-memory does not survive
   across the sync Alembic connection and the async aiosqlite engine).
2. Runs the full Alembic migration chain (currently 0001 + 0002).
3. Builds a fresh :class:`SqliteEngineFactory` bound to that file.
4. Disposes the engine on teardown.

This is the "parity gate" referenced by the Phase B plan: every SQLite
repository test uses the same fixture so the migration → engine → repo
contract is exercised end-to-end exactly once per test.
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

import pytest

from app.repositories.sqlite.engine import SqliteEngineFactory
from app.repositories.sqlite.migrations.runner import upgrade_to_head


@pytest.fixture
async def sqlite_engine_factory(tmp_path: Path) -> AsyncIterator[SqliteEngineFactory]:
    """Migrated, isolated SQLite database wrapped in a fresh engine factory."""
    db_path = tmp_path / "phase_b_parity.db"
    upgrade_to_head(f"sqlite:///{db_path}")
    factory = SqliteEngineFactory(db_path=str(db_path))
    try:
        yield factory
    finally:
        await factory.dispose()
