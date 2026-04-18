"""Programmatic Alembic runner for the SQLite (desktop) database.

Exposes :func:`upgrade_to_head` so the test suite, Phase B repositories,
and the future Electron/Phase B desktop runtime can apply migrations
without shelling out to the Alembic CLI.

The runner is synchronous because Alembic itself is synchronous; callers
that live in async contexts can wrap it with :func:`asyncio.to_thread`.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

_MIGRATIONS_DIR = Path(__file__).resolve().parent
_ALEMBIC_INI = _MIGRATIONS_DIR / "alembic.ini"


def build_alembic_config(url: str) -> Config:
    """Build an Alembic :class:`Config` rooted at this package.

    ``url`` should be a SQLAlchemy URL (sync flavor — e.g.
    ``sqlite:///path/to/db.sqlite``). The runner will pass it to env.py
    via :attr:`Config.attributes`, bypassing the application settings.
    """
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    # env.py picks this up first, before settings or -x args.
    cfg.attributes["sqlalchemy.url"] = url
    return cfg


def upgrade_to_head(url: str) -> None:
    """Apply all pending migrations against ``url``."""
    command.upgrade(build_alembic_config(url), "head")


def downgrade_to_base(url: str) -> None:
    """Revert all migrations against ``url``. Test/recovery use only."""
    command.downgrade(build_alembic_config(url), "base")


__all__ = [
    "build_alembic_config",
    "downgrade_to_base",
    "upgrade_to_head",
]
