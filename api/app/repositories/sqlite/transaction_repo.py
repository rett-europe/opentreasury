"""SQLite implementation of :class:`app.repositories.protocols.TransactionRepository`.

This is the largest SQLite repository: it exposes both read paths (list,
get, count_*, aggregate, report/export queries) and write paths (create,
replace + soft-delete via document-shape preservation).

The mapping between snake_case columns and the canonical Cosmos
camelCase document shape lives in the private ``_to_doc`` / ``_from_doc``
helpers per the Phase B B-1 mapping decision (2026-04-18). Service-tier
code consuming the returned dicts cannot tell whether the data came from
Cosmos or SQLite — that is the "functional parity" gate (spec §4.3.1).

Notable invariants preserved in the mapping layer:

* **Signed amount semantics** (AS-001..AS-006) — services compute the
  signed amount before calling ``create``/``replace``; the repo stores
  it verbatim and round-trips it through :class:`Decimal`.
* **Soft-delete invariant** — every read path filters ``is_deleted = 0``
  unless ``include_deleted=True``.
* **Decimal/NUMERIC discipline** — money values never become floats.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.models.domain import TransactionType
from app.repositories.sqlite._mapping import (
    bool_from_int,
    dumps_json,
    from_decimal,
    loads_json,
    parse_iso,
    to_decimal,
    to_iso,
)
from app.repositories.sqlite.engine import SqliteEngineFactory, get_engine_factory


# ---------------------------------------------------------------------------
# Filter builder — mirrors ``cosmos.transaction_repo._build_filter_conditions``.
# Keeping the supported keys identical guarantees that the same ``filters``
# dict produced by the service layer hits the same set of rows on either
# backend (B-1 parity contract).
# ---------------------------------------------------------------------------


def _build_filter_conditions(
    partition_key: str,
    filters: dict | None,
    include_deleted: bool,
) -> tuple[list[str], dict[str, Any]]:
    conditions: list[str] = ["partition_key = :pk"]
    params: dict[str, Any] = {"pk": partition_key}

    if not include_deleted:
        conditions.append("is_deleted = 0")

    if filters:
        if "accountId" in filters:
            conditions.append("account_id = :account_id")
            params["account_id"] = filters["accountId"]
        if "categoryId" in filters:
            conditions.append("category_id = :category_id")
            params["category_id"] = filters["categoryId"]
        if "subcategoryId" in filters:
            conditions.append("subcategory_id = :subcategory_id")
            params["subcategory_id"] = filters["subcategoryId"]
        if "tagId" in filters:
            # Cosmos: ARRAY_CONTAINS(c.tagIds, @tagId).
            # SQLite equivalent: json_each over the tag_ids column.
            conditions.append("EXISTS (SELECT 1 FROM json_each(tag_ids) WHERE json_each.value = :tag_id)")
            params["tag_id"] = filters["tagId"]
        if "search" in filters:
            conditions.append(
                "(LOWER(COALESCE(bank_description, '')) LIKE :search " "OR LOWER(COALESCE(detail, '')) LIKE :search)"
            )
            params["search"] = f"%{filters['search'].lower()}%"
        if "amountMin" in filters:
            conditions.append("amount >= :amount_min")
            params["amount_min"] = filters["amountMin"]
        if "amountMax" in filters:
            conditions.append("amount <= :amount_max")
            params["amount_max"] = filters["amountMax"]
        if "transactionType" in filters:
            conditions.append("transaction_type = :transaction_type")
            params["transaction_type"] = filters["transactionType"]
        if "categorizationStatus" in filters:
            conditions.append("categorization_status = :categorization_status")
            params["categorization_status"] = filters["categorizationStatus"]
        if "reviewStatus" in filters:
            conditions.append("review_status = :review_status")
            params["review_status"] = filters["reviewStatus"]

    return conditions, params


# ---------------------------------------------------------------------------
# Continuation token (opaque). Same shape as the audit repo.
# ---------------------------------------------------------------------------


def _encode_offset(offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()


def _decode_offset(token: str | None) -> int:
    if not token:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        return int(payload.get("offset", 0))
    except (ValueError, KeyError, json.JSONDecodeError):
        return 0


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class SqliteTransactionRepository:
    def __init__(self, engine_factory: SqliteEngineFactory | None = None) -> None:
        self._engine_factory = engine_factory or get_engine_factory()

    # ------------------------------------------------------------------
    # Mapping helpers (single canonical pair per repo, per B-1 decision).
    # ------------------------------------------------------------------
    @staticmethod
    def _to_doc(row: Any) -> dict:
        return {
            "id": row["id"],
            "type": "transaction",
            "partitionKey": row["partition_key"],
            "date": row["date"],
            "year": row["year"],
            "month": row["month"],
            "amount": to_decimal(row["amount"]),
            "transactionType": row["transaction_type"],
            "accountId": row["account_id"],
            "categoryId": row["category_id"],
            "subcategoryId": row["subcategory_id"],
            "categorizationStatus": row["categorization_status"],
            "reviewStatus": row["review_status"],
            "reviewedBy": row["reviewed_by"],
            "reviewedByName": row["reviewed_by_name"],
            "reviewedByEmail": row["reviewed_by_email"],
            "reviewedAt": to_iso(row["reviewed_at"]),
            "sourceReference": row["source_reference"],
            "counterpartyName": row["counterparty_name"],
            "counterpartyReference": row["counterparty_reference"],
            "description": row["description"],
            "bankDescription": row["bank_description"],
            "detail": row["detail"],
            "reference": row["reference"],
            "originalAmount": to_decimal(row["original_amount"]),
            "originalDate": row["original_date"],
            "notes": loads_json(row["notes"]) or [],
            "tagIds": loads_json(row["tag_ids"]) or [],
            "isSplit": bool_from_int(row["is_split"]),
            "splitLines": loads_json(row["split_lines"]) or [],
            "createdBy": row["created_by"],
            "createdAt": to_iso(row["created_at"]),
            "updatedBy": row["updated_by"],
            "updatedAt": to_iso(row["updated_at"]),
            "version": row["version"],
            "isDeleted": bool_from_int(row["is_deleted"]),
            "deletedAt": to_iso(row["deleted_at"]),
        }

    @staticmethod
    def _from_doc(doc: dict) -> dict:
        return {
            "id": doc["id"],
            "partition_key": doc["partitionKey"],
            "date": doc["date"],
            "year": int(doc["year"]),
            "month": int(doc["month"]),
            "amount": from_decimal(doc["amount"]),
            "transaction_type": doc.get("transactionType"),
            "account_id": doc.get("accountId"),
            "category_id": doc.get("categoryId"),
            "subcategory_id": doc.get("subcategoryId"),
            "categorization_status": doc.get("categorizationStatus"),
            "review_status": doc.get("reviewStatus"),
            "reviewed_by": doc.get("reviewedBy"),
            "reviewed_by_name": doc.get("reviewedByName"),
            "reviewed_by_email": doc.get("reviewedByEmail"),
            "reviewed_at": parse_iso(doc.get("reviewedAt")),
            "source_reference": doc.get("sourceReference"),
            "counterparty_name": doc.get("counterpartyName"),
            "counterparty_reference": doc.get("counterpartyReference"),
            "description": doc.get("description"),
            "bank_description": doc.get("bankDescription"),
            "detail": doc.get("detail"),
            "reference": doc.get("reference"),
            "original_amount": from_decimal(doc.get("originalAmount")),
            "original_date": doc.get("originalDate"),
            "notes": dumps_json(doc.get("notes") or []),
            "tag_ids": dumps_json(doc.get("tagIds") or []),
            "is_split": 1 if doc.get("isSplit") else 0,
            "split_lines": dumps_json(doc.get("splitLines") or []),
            "created_by": doc.get("createdBy") or "",
            "created_at": parse_iso(doc.get("createdAt")) or datetime.now(timezone.utc),
            "updated_by": doc.get("updatedBy"),
            "updated_at": parse_iso(doc.get("updatedAt")),
            "is_deleted": 1 if doc.get("isDeleted") else 0,
            "deleted_at": parse_iso(doc.get("deletedAt")),
        }

    # ------------------------------------------------------------------
    # Read paths
    # ------------------------------------------------------------------
    async def list_by_partition(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
        page_size: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        conditions, params = _build_filter_conditions(partition_key, filters, include_deleted)
        offset = _decode_offset(continuation_token)
        params["limit"] = page_size
        params["offset"] = offset

        where = " AND ".join(conditions)
        query = (
            f"SELECT * FROM transactions WHERE {where} " "ORDER BY date DESC, id DESC " "LIMIT :limit OFFSET :offset"
        )

        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params)
            items = [self._to_doc(r) for r in result.mappings()]

        next_token = _encode_offset(offset + len(items)) if len(items) == page_size else None
        return items, next_token

    async def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM transactions " "WHERE id = :id AND partition_key = :pk"),
                {"id": item_id, "pk": partition_key},
            )
            row = result.mappings().first()
        if row is None:
            return None
        return self._to_doc(row)

    async def query_for_report(
        self,
        year: int,
        month: int | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
        # Cosmos returns a projection (categoryId, subcategoryId, accountId,
        # amount, month, transactionType, isSplit, splitLines). We mirror
        # that exactly so the report service sees the same row shape.
        params: dict[str, Any] = {}
        clauses: list[str] = ["is_deleted = 0"]
        if month is not None:
            clauses.append("partition_key = :pk")
            params["pk"] = f"{year:04d}-{month:02d}"
        else:
            clauses.append("year = :year")
            params["year"] = year
        if account_id:
            clauses.append("account_id = :account_id")
            params["account_id"] = account_id
        where = " AND ".join(clauses)

        query = (
            "SELECT category_id, subcategory_id, account_id, amount, month, "
            "       transaction_type, is_split, split_lines "
            f"FROM transactions WHERE {where}"
        )
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params)
            return [
                {
                    "categoryId": r["category_id"],
                    "subcategoryId": r["subcategory_id"],
                    "accountId": r["account_id"],
                    "amount": to_decimal(r["amount"]),
                    "month": r["month"],
                    "transactionType": r["transaction_type"],
                    "isSplit": bool_from_int(r["is_split"]),
                    "splitLines": loads_json(r["split_lines"]) or [],
                }
                for r in result.mappings()
            ]

    async def query_for_export(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict]:
        params: dict[str, Any] = {"date_from": date_from, "date_to": date_to}
        clauses = ["date >= :date_from", "date <= :date_to", "is_deleted = 0"]
        if account_id:
            clauses.append("account_id = :account_id")
            params["account_id"] = account_id
        if category_id:
            clauses.append("category_id = :category_id")
            params["category_id"] = category_id
        where = " AND ".join(clauses)
        query = f"SELECT * FROM transactions WHERE {where} ORDER BY date ASC"
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params)
            return [self._to_doc(r) for r in result.mappings()]

    async def count_by_account(self, account_id: str) -> int:
        return await self._count(
            "account_id = :account_id AND is_deleted = 0",
            {"account_id": account_id},
        )

    async def count_by_category(self, category_id: str) -> int:
        return await self._count(
            "category_id = :category_id AND is_deleted = 0",
            {"category_id": category_id},
        )

    async def count_by_subcategory(self, category_id: str, subcategory_id: str) -> int:
        return await self._count(
            "category_id = :category_id AND subcategory_id = :subcategory_id " "AND is_deleted = 0",
            {"category_id": category_id, "subcategory_id": subcategory_id},
        )

    async def count_by_tag(self, tag_id: str) -> int:
        return await self._count(
            "EXISTS (SELECT 1 FROM json_each(tag_ids) WHERE json_each.value = :tag_id) " "AND is_deleted = 0",
            {"tag_id": tag_id},
        )

    async def _count(self, where: str, params: dict) -> int:
        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT COUNT(1) AS c FROM transactions WHERE {where}"),
                params,
            )
            row = result.mappings().first()
            return int(row["c"]) if row else 0

    async def aggregate_filtered(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
    ) -> dict:
        conditions, params = _build_filter_conditions(partition_key, filters, include_deleted)
        where = " AND ".join(conditions)
        query = "SELECT amount, transaction_type, category_id, is_split " f"FROM transactions WHERE {where}"

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        transaction_count = 0
        uncategorized_count = 0

        engine = self._engine_factory.get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params)
            for row in result.mappings():
                transaction_count += 1
                tx_type = row["transaction_type"]
                amount = abs(to_decimal(row["amount"]) or Decimal("0"))
                if tx_type == TransactionType.INCOME.value:
                    total_income += amount
                elif tx_type == TransactionType.EXPENSE.value:
                    total_expenses += amount
                # transfer / refund: excluded from totals (Cosmos parity).
                if not row["category_id"] and not bool_from_int(row["is_split"]):
                    uncategorized_count += 1

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "transaction_count": transaction_count,
            "uncategorized_count": uncategorized_count,
        }

    # ------------------------------------------------------------------
    # Write paths
    # ------------------------------------------------------------------
    async def create(self, document: dict) -> dict:
        params = self._from_doc(document)
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(text(_INSERT_SQL), params)
        # Re-read so the response carries server-side defaults (version=1, …)
        # and the canonical doc shape produced by ``_to_doc``.
        async with engine.connect() as conn:
            row = (
                (
                    await conn.execute(
                        text("SELECT * FROM transactions " "WHERE id = :id AND partition_key = :pk"),
                        {"id": document["id"], "pk": document["partitionKey"]},
                    )
                )
                .mappings()
                .first()
            )
        return self._to_doc(row)

    async def replace(self, item_id: str, document: dict) -> dict:
        # Cosmos's ``replace_item`` overwrites the whole document. We mirror
        # that by UPDATE-ing every column from ``_from_doc``. ``isDeleted=True``
        # in the document is the soft-delete path the service uses today;
        # the row stays in place so the audit trail and cross-references
        # remain valid (spec §4.3 — soft-delete behavior).
        params = self._from_doc({**document, "id": item_id})
        engine = self._engine_factory.get_engine()
        async with engine.begin() as conn:
            await conn.execute(text(_UPDATE_SQL), params)
        async with engine.connect() as conn:
            row = (
                (
                    await conn.execute(
                        text("SELECT * FROM transactions WHERE id = :id"),
                        {"id": item_id},
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            raise KeyError(f"transaction {item_id!r} not found")
        return self._to_doc(row)


# ---------------------------------------------------------------------------
# Statement constants (extracted to keep the methods readable).
# ---------------------------------------------------------------------------

_INSERT_SQL = (
    "INSERT INTO transactions ("
    " id, partition_key, date, year, month, amount, transaction_type,"
    " account_id, category_id, subcategory_id, categorization_status,"
    " review_status, reviewed_by, reviewed_by_name, reviewed_by_email,"
    " reviewed_at, source_reference, counterparty_name,"
    " counterparty_reference, description, bank_description, detail,"
    " reference, original_amount, original_date, notes, tag_ids,"
    " is_split, split_lines, created_by, created_at, updated_by,"
    " updated_at, is_deleted, deleted_at"
    ") VALUES ("
    " :id, :partition_key, :date, :year, :month, :amount, :transaction_type,"
    " :account_id, :category_id, :subcategory_id, :categorization_status,"
    " :review_status, :reviewed_by, :reviewed_by_name, :reviewed_by_email,"
    " :reviewed_at, :source_reference, :counterparty_name,"
    " :counterparty_reference, :description, :bank_description, :detail,"
    " :reference, :original_amount, :original_date, :notes, :tag_ids,"
    " :is_split, :split_lines, :created_by, :created_at, :updated_by,"
    " :updated_at, :is_deleted, :deleted_at"
    ")"
)

_UPDATE_SQL = (
    "UPDATE transactions SET"
    " partition_key = :partition_key,"
    " date = :date,"
    " year = :year,"
    " month = :month,"
    " amount = :amount,"
    " transaction_type = :transaction_type,"
    " account_id = :account_id,"
    " category_id = :category_id,"
    " subcategory_id = :subcategory_id,"
    " categorization_status = :categorization_status,"
    " review_status = :review_status,"
    " reviewed_by = :reviewed_by,"
    " reviewed_by_name = :reviewed_by_name,"
    " reviewed_by_email = :reviewed_by_email,"
    " reviewed_at = :reviewed_at,"
    " source_reference = :source_reference,"
    " counterparty_name = :counterparty_name,"
    " counterparty_reference = :counterparty_reference,"
    " description = :description,"
    " bank_description = :bank_description,"
    " detail = :detail,"
    " reference = :reference,"
    " original_amount = :original_amount,"
    " original_date = :original_date,"
    " notes = :notes,"
    " tag_ids = :tag_ids,"
    " is_split = :is_split,"
    " split_lines = :split_lines,"
    " updated_by = :updated_by,"
    " updated_at = :updated_at,"
    " is_deleted = :is_deleted,"
    " deleted_at = :deleted_at,"
    " version = version + 1"
    " WHERE id = :id"
)
