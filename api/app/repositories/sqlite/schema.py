"""SQLAlchemy schema definition for the OpenTreasury SQLite database.

This module is the **single source of truth** for the SQLite schema in
desktop mode (Electron + SQLite spec §4.3, §6.5). Alembic's
``env.py`` imports :data:`metadata` from here in autogenerate mode, and
the unit tests assert the structure of the resulting schema.

Schema design notes:

* Mirrors the Cosmos document shape closely so service-layer logic can
  treat row-dicts and Cosmos documents interchangeably (spec §4.1).
* ``amount`` columns use ``NUMERIC`` to preserve signed decimal semantics
  (no float rounding for currency values).
* Soft-delete columns (``is_deleted``, ``deleted_at``) match the Cosmos
  ``isDeleted`` invariant called out in spec §4.3.
* Every mutable table carries ``updated_at`` and ``version`` for the
  optimistic-concurrency strategy planned in Phase D (spec §7.1).
* ``audit_log.actor_source`` is the discriminator from spec §6.5.
* ``app_identity`` is new for desktop mode: stores the user-asserted
  display name + ``actor_source`` for the local user (spec §6.2).
* ``users`` is created **empty** and reserved for the future in-app RBAC
  enhancement noted in spec §4.3 / §6.4.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
)

# Naming convention keeps Alembic's autogenerate output deterministic across
# platforms — important because dev machines and CI may produce different
# anonymous constraint names otherwise.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------------------------------------------------------------------------
# Reference data — accounts, tags, and other simple lookup items.
# In Cosmos this is a single container partitioned by `type`; in SQLite we
# keep the same shape (single table with a `type` discriminator) so the
# repository protocol is satisfiable by both backends without divergence.
# ---------------------------------------------------------------------------
reference_data = Table(
    "reference_data",
    metadata,
    Column("id", String, primary_key=True),
    Column("type", String, nullable=False),  # e.g. "account", "tag"
    Column("name", String, nullable=False),
    Column("description", Text, nullable=True),
    Column("sort_order", Integer, nullable=True),
    # Free-form JSON for type-specific fields (e.g. account currency).
    # SQLAlchemy's JSON type maps to TEXT on SQLite with json1 codec.
    Column("attributes", JSON, nullable=True),
    Column("created_by", String, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column("updated_by", String, nullable=True),
    Column("updated_at", DateTime, nullable=True),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("is_deleted", Integer, nullable=False, server_default="0"),
    Column("deleted_at", DateTime, nullable=True),
    Index("ix_reference_data_type", "type"),
    Index("ix_reference_data_type_sort", "type", "sort_order"),
)


# ---------------------------------------------------------------------------
# Categories (income/expense) with embedded subcategories as JSON, mirroring
# the Cosmos document shape.
# ---------------------------------------------------------------------------
categories = Table(
    "categories",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", Text, nullable=True),
    Column("category_type", String, nullable=False),  # "income" | "expense"
    Column("sort_order", Integer, nullable=True),
    Column("subcategories", JSON, nullable=True),  # list[{id, name}]
    Column("created_by", String, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column("updated_by", String, nullable=True),
    Column("updated_at", DateTime, nullable=True),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("is_deleted", Integer, nullable=False, server_default="0"),
    Column("deleted_at", DateTime, nullable=True),
    CheckConstraint(
        "category_type IN ('income', 'expense')",
        name="category_type_valid",
    ),
)


# ---------------------------------------------------------------------------
# Transactions — the financial ledger.
# Signed amount semantics (spec §4.3): the `amount` column stores the value
# as written by the service layer; the sign convention (positive=income,
# negative=expense) is enforced at the service tier and preserved here.
# ---------------------------------------------------------------------------
transactions = Table(
    "transactions",
    metadata,
    Column("id", String, primary_key=True),
    Column("partition_key", String, nullable=False),  # e.g. "tx-{accountId}"
    Column("date", String, nullable=False),  # ISO-8601 date (YYYY-MM-DD)
    Column("year", Integer, nullable=False),
    Column("month", Integer, nullable=False),
    Column("amount", Numeric(18, 2), nullable=False),
    Column("transaction_type", String, nullable=False),  # "income" | "expense"
    Column("account_id", String, nullable=True),
    Column("category_id", String, nullable=True),
    Column("subcategory_id", String, nullable=True),
    Column("categorization_status", String, nullable=True),
    Column("review_status", String, nullable=True),
    Column("reviewed_by", String, nullable=True),
    Column("reviewed_by_name", String, nullable=True),
    Column("reviewed_at", DateTime, nullable=True),
    Column("source_reference", String, nullable=True),
    Column("counterparty_name", String, nullable=True),
    Column("counterparty_reference", String, nullable=True),
    Column("description", Text, nullable=True),
    Column("reference", String, nullable=True),
    Column("original_amount", Numeric(18, 2), nullable=True),
    Column("original_date", String, nullable=True),
    Column("notes", JSON, nullable=True),  # list[note]
    Column("tags", JSON, nullable=True),  # list[tag_id]
    Column("created_by", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_by", String, nullable=True),
    Column("updated_at", DateTime, nullable=True),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("is_deleted", Integer, nullable=False, server_default="0"),
    Column("deleted_at", DateTime, nullable=True),
    CheckConstraint(
        "transaction_type IN ('income', 'expense')",
        name="transaction_type_valid",
    ),
    Index("ix_transactions_partition_key", "partition_key"),
    Index("ix_transactions_account_id", "account_id"),
    Index("ix_transactions_category_id", "category_id"),
    Index("ix_transactions_year_month", "year", "month"),
    Index("ix_transactions_date", "date"),
)


# ---------------------------------------------------------------------------
# Audit log — append-only at the service layer (spec §8.4).
# `actor_source` is the trust-tier discriminator from spec §6.5.
# ---------------------------------------------------------------------------
audit_log = Table(
    "audit_log",
    metadata,
    Column("id", String, primary_key=True),
    Column("entity_type", String, nullable=False),
    Column("entity_id", String, nullable=False),
    Column("action", String, nullable=False),  # Create | Update | Delete | Restore
    Column("changed_by", String, nullable=False),
    Column("changed_by_name", String, nullable=True),
    Column("changed_by_email", String, nullable=True),
    # actor_source — trust tier of the recorded identity (spec §6.5).
    # Allowed values: os_username | app_prompt | microsoft_account | entra_id
    Column("actor_source", String, nullable=False),
    Column("changed_at", DateTime, nullable=False),
    Column("old_values", JSON, nullable=True),
    Column("new_values", JSON, nullable=True),
    CheckConstraint(
        "actor_source IN ('os_username', 'app_prompt', 'microsoft_account', 'entra_id')",
        name="actor_source_valid",
    ),
    Index("ix_audit_log_entity_type", "entity_type"),
    Index("ix_audit_log_entity_id", "entity_id"),
    Index("ix_audit_log_changed_at", "changed_at"),
)


# ---------------------------------------------------------------------------
# app_identity — the locally asserted user identity for the desktop runtime
# (spec §4.3, §6.2). At most one row in normal use; the row carries the
# user's display name and the source from which it was obtained so the
# audit layer can stamp every entry with a consistent `actor_source`.
# ---------------------------------------------------------------------------
app_identity = Table(
    "app_identity",
    metadata,
    Column("id", String, primary_key=True),
    Column("display_name", String, nullable=False),
    Column("email", String, nullable=True),
    # Same discriminator vocabulary as audit_log.actor_source.
    Column("actor_source", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=True),
    CheckConstraint(
        "actor_source IN ('os_username', 'app_prompt', 'microsoft_account', 'entra_id')",
        name="app_identity_actor_source_valid",
    ),
)


# ---------------------------------------------------------------------------
# users — RESERVED, empty in Phase A (spec §4.3, §6.4). The future in-app
# RBAC enhancement will populate this table; for now it exists so migrations
# don't need a follow-up to add it later.
# ---------------------------------------------------------------------------
users = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True),
    Column("display_name", String, nullable=False),
    Column("email", String, nullable=True),
    Column("role", String, nullable=False, server_default="Admin"),  # future RBAC
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=True),
)


# ---------------------------------------------------------------------------
# user_preferences — keyed by the user's stable identifier (Cosmos `oid`
# in cloud mode; the `app_identity.id` in desktop Local mode; the MS account
# id in Team mode).
# ---------------------------------------------------------------------------
user_preferences = Table(
    "user_preferences",
    metadata,
    Column("user_oid", String, primary_key=True),
    Column("preferences", JSON, nullable=False),
    Column("updated_at", DateTime, nullable=True),
    Column("version", Integer, nullable=False, server_default="1"),
)


__all__ = [
    "NAMING_CONVENTION",
    "app_identity",
    "audit_log",
    "categories",
    "metadata",
    "reference_data",
    "transactions",
    "user_preferences",
    "users",
]


def expected_table_names() -> set[str]:
    """Return the set of table names this schema should produce.

    Used by tests as a contract assertion against the Alembic-applied DB.
    """
    return {t.name for t in metadata.sorted_tables}
