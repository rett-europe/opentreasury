"""Phase B — schema parity gap-fill.

Closes the gap between the minimal Phase A schema and the fields that the
existing service-layer + Cosmos repositories already read/write. See
``docs/specs/electron-sqlite-spec.md`` §4.3.2 for the inventory and the
``Phase B schema-gap inventory`` decision (2026-04-18) in
``.squad/decisions.md``.

Changes in this revision:

* ``transactions``: add ``is_split`` (bool/int), ``split_lines`` (JSON),
  ``bank_description`` (text), ``detail`` (text), ``reviewed_by_email``
  (string); rename ``tags`` → ``tag_ids`` so the column matches the
  Cosmos ``tagIds`` document field one-for-one.
* ``audit_log``: add ``metadata`` (JSON) for free-form context.

Phase A has not shipped to production users, so the ``tags`` → ``tag_ids``
rename is performed in place via ``batch_alter_table`` (SQLite cannot
rename columns without a table rebuild; Alembic's batch mode handles
this transparently).

Revision ID: 0002_phase_b_schema_parity
Revises: 0001_phase_a_initial
Create Date: 2026-04-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase_b_schema_parity"
down_revision: Union[str, None] = "0001_phase_a_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # transactions: add new parity columns and rename `tags` → `tag_ids`.
    # We avoid Alembic batch mode here because batch reflection consults
    # ``target_metadata`` and the new metadata has already renamed ``tags``,
    # which trips batch's column lookup. SQLite ≥3.35 supports DROP COLUMN
    # and RENAME COLUMN natively, so direct DDL is both simpler and safer.
    op.add_column(
        "transactions",
        sa.Column("is_split", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("transactions", sa.Column("split_lines", sa.JSON(), nullable=True))
    op.add_column("transactions", sa.Column("bank_description", sa.Text(), nullable=True))
    op.add_column("transactions", sa.Column("detail", sa.Text(), nullable=True))
    op.add_column("transactions", sa.Column("reviewed_by_email", sa.String(), nullable=True))
    op.execute("ALTER TABLE transactions RENAME COLUMN tags TO tag_ids")

    # audit_log: add free-form metadata column.
    op.add_column("audit_log", sa.Column("metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.execute("ALTER TABLE audit_log DROP COLUMN metadata")

    op.execute("ALTER TABLE transactions RENAME COLUMN tag_ids TO tags")
    op.execute("ALTER TABLE transactions DROP COLUMN reviewed_by_email")
    op.execute("ALTER TABLE transactions DROP COLUMN detail")
    op.execute("ALTER TABLE transactions DROP COLUMN bank_description")
    op.execute("ALTER TABLE transactions DROP COLUMN split_lines")
    op.execute("ALTER TABLE transactions DROP COLUMN is_split")
