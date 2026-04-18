"""Phase A — initial OpenTreasury SQLite (desktop) schema.

Creates the full Phase A schema (spec §4.3, §6.5):
``transactions``, ``categories``, ``reference_data``, ``audit_log``
(with ``actor_source``), ``app_identity``, reserved-empty ``users``,
``user_preferences``.

This migration carries its **own frozen snapshot** of the schema as it
existed at the end of Phase A, rather than re-reading the live
:mod:`app.repositories.sqlite.schema` module. That keeps the migration
history immutable as the schema evolves in later phases (spec §9, Phase B
schema-parity migration ``0002_phase_b_schema_parity``).

Revision ID: 0001_phase_a_initial
Revises:
Create Date: 2026-04-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_phase_a_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reference_data",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_reference_data_type", "reference_data", ["type"])
    op.create_index(
        "ix_reference_data_type_sort",
        "reference_data",
        ["type", "sort_order"],
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_type", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("subcategories", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "category_type IN ('income', 'expense')",
            name="ck_categories_category_type_valid",
        ),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("partition_key", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=True),
        sa.Column("category_id", sa.String(), nullable=True),
        sa.Column("subcategory_id", sa.String(), nullable=True),
        sa.Column("categorization_status", sa.String(), nullable=True),
        sa.Column("review_status", sa.String(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_by_name", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("source_reference", sa.String(), nullable=True),
        sa.Column("counterparty_name", sa.String(), nullable=True),
        sa.Column("counterparty_reference", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("original_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("original_date", sa.String(), nullable=True),
        sa.Column("notes", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_transaction_type_valid",
        ),
    )
    op.create_index("ix_transactions_partition_key", "transactions", ["partition_key"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_year_month", "transactions", ["year", "month"])
    op.create_index("ix_transactions_date", "transactions", ["date"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        sa.Column("changed_by_name", sa.String(), nullable=True),
        sa.Column("changed_by_email", sa.String(), nullable=True),
        sa.Column("actor_source", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "actor_source IN ('os_username', 'app_prompt', 'microsoft_account', 'entra_id')",
            name="ck_audit_log_actor_source_valid",
        ),
    )
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"])
    op.create_index("ix_audit_log_changed_at", "audit_log", ["changed_at"])

    op.create_table(
        "app_identity",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("actor_source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "actor_source IN ('os_username', 'app_prompt', 'microsoft_account', 'entra_id')",
            name="ck_app_identity_app_identity_actor_source_valid",
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="Admin"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "user_preferences",
        sa.Column("user_oid", sa.String(), primary_key=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("users")
    op.drop_table("app_identity")
    op.drop_index("ix_audit_log_changed_at", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_type", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_year_month", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_partition_key", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_index("ix_reference_data_type_sort", table_name="reference_data")
    op.drop_index("ix_reference_data_type", table_name="reference_data")
    op.drop_table("reference_data")
