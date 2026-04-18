"""Alembic migrations for the OpenTreasury SQLite (desktop) database.

This package is the Phase A migration framework called out in
``docs/specs/electron-sqlite-spec.md`` §9 Phase A.

Run migrations programmatically with
:func:`app.repositories.sqlite.migrations.runner.upgrade_to_head`, or via
the Alembic CLI with ``ALEMBIC_CONFIG=api/app/repositories/sqlite/migrations/alembic.ini``.
"""
