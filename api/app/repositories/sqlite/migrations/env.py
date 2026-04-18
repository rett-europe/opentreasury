"""Alembic environment for the OpenTreasury SQLite (desktop) database.

Resolves the target URL at runtime from :data:`app.config.settings`,
or accepts an explicit override via ``config.attributes["sqlalchemy.url"]``
or the ``-x url=...`` CLI option. This lets the test suite point Alembic
at an in-memory SQLite database without mutating environment state.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.repositories.sqlite.engine import _build_url
from app.repositories.sqlite.schema import metadata as target_metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_url() -> str:
    # Priority: programmatic attribute > -x url=... > settings.SQLITE_DB_PATH.
    attr_url = config.attributes.get("sqlalchemy.url")
    if attr_url:
        return attr_url
    x_args = context.get_x_argument(as_dictionary=True)
    if "url" in x_args:
        return x_args["url"]
    # Late import so simply importing this module doesn't force
    # ``Settings()`` to instantiate (which requires Cosmos env vars).
    from app.config import settings

    return _build_url(settings.SQLITE_DB_PATH)


def run_migrations_offline() -> None:
    """Run migrations without a DB connection (emits SQL)."""
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite needs batch mode for ALTER TABLE
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    # Build a sync engine — Alembic's runner is synchronous. We strip the
    # async driver name (``+aiosqlite``) so SQLAlchemy uses the stdlib
    # ``sqlite3`` driver for the duration of the migration.
    url = _resolve_url().replace("sqlite+aiosqlite://", "sqlite://")
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = url
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
