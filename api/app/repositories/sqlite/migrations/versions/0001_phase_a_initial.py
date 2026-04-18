"""Phase A — initial OpenTreasury SQLite (desktop) schema.

Creates the full Phase A schema (spec §4.3, §6.5):
``transactions``, ``categories``, ``reference_data``, ``audit_log``
(with ``actor_source``), ``app_identity``, reserved-empty ``users``,
``user_preferences``.

The schema is sourced from :mod:`app.repositories.sqlite.schema` so this
migration cannot drift from the metadata that the application reads.

Revision ID: 0001_phase_a_initial
Revises:
Create Date: 2026-04-18
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.repositories.sqlite.schema import metadata

# revision identifiers, used by Alembic.
revision: str = "0001_phase_a_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    metadata.drop_all(bind=bind)
