from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.domain import AuditAction, CategorizationStatus

if TYPE_CHECKING:
    from app.repositories.protocols import CategoryRepository, TransactionRepository
    from app.services.audit_service import AuditService


class SplitService:
    def __init__(
        self,
        *,
        repo: TransactionRepository,
        audit_service: AuditService,
        category_repo: CategoryRepository,
    ):
        self._repo = repo
        self._audit = audit_service
        self._category_repo = category_repo

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _validate_category(
        self,
        category_id: str | None,
        subcategory_id: str | None,
        transaction_type: str,
    ) -> None:
        """Validate category/subcategory (same pattern as TransactionService)."""
        if category_id is None:
            if subcategory_id is not None:
                raise ValueError("subcategoryId can only be set when categoryId is also set")
            return

        cat = await self._category_repo.get_by_id(category_id)
        if not cat or not cat.get("isActive", True):
            raise ValueError(f"Category '{category_id}' not found or inactive")

        if subcategory_id is not None:
            subs = cat.get("subcategories", [])
            match = next(
                (s for s in subs if s["id"] == subcategory_id and s.get("isActive", True)),
                None,
            )
            if match is None:
                raise ValueError(
                    f"Subcategory '{subcategory_id}' does not belong to " f"category '{category_id}' or is inactive"
                )

    async def _get_active_transaction(self, transaction_id: str, year: int, month: int) -> dict | None:
        partition_key = f"{year:04d}-{month:02d}"
        item = await self._repo.get_by_id(transaction_id, partition_key)
        if not item or item.get("isDeleted"):
            return None
        return item

    async def _validate_lines(
        self,
        lines: list[dict],
        parent_amount: Decimal,
        transaction_type: str,
    ) -> None:
        """Validate split line list: count, sum, line amounts, and categories."""
        if len(lines) < 2:
            raise ValueError("A split must have at least 2 lines")
        if len(lines) > 20:
            raise ValueError("A split must have at most 20 lines")

        line_sum = Decimal("0")
        for line in lines:
            amount = Decimal(str(line["amount"]))
            if amount <= 0:
                raise ValueError("Each split line amount must be greater than 0")
            line_sum += amount
        if line_sum != abs(parent_amount):
            raise ValueError(f"Split line amounts ({line_sum}) must equal " f"the parent amount ({abs(parent_amount)})")

        for line in lines:
            await self._validate_category(
                line.get("categoryId"),
                line.get("subcategoryId"),
                transaction_type,
            )

    def _build_split_lines(self, lines: list[dict], parent_amount: Decimal) -> tuple[list[dict], list[str]]:
        """Build split line dicts and collect unique category IDs."""
        sign = Decimal("1") if parent_amount >= 0 else Decimal("-1")

        split_lines: list[dict] = []
        category_ids: set[str] = set()
        for idx, line in enumerate(lines):
            amt = Decimal(str(line["amount"]))
            signed_amount = float(amt * sign)
            cat_id = line.get("categoryId")
            sl = {
                "id": str(uuid4()),
                "amount": signed_amount,
                "categoryId": cat_id,
                "subcategoryId": line.get("subcategoryId"),
                "tagIds": line.get("tagIds", []),
                "detail": line.get("detail"),
                "sortOrder": idx + 1,
            }
            split_lines.append(sl)
            if cat_id:
                category_ids.add(cat_id)

        return split_lines, sorted(category_ids)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def split_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        lines: list[dict],
        user_id: str,
        user_name: str,
    ) -> dict:
        """Create a split on a non-split transaction."""
        existing = await self._get_active_transaction(transaction_id, year, month)
        if not existing:
            return None

        if existing.get("isSplit"):
            raise ValueError("Transaction is already split. Use PUT to update.")

        parent_amount = Decimal(str(existing["amount"]))
        txn_type = existing.get("transactionType", "expense")

        await self._validate_lines(lines, parent_amount, txn_type)
        split_lines, split_category_ids = self._build_split_lines(lines, parent_amount)

        now = datetime.now(timezone.utc).isoformat()
        existing["isSplit"] = True
        existing["splitCount"] = len(split_lines)
        existing["splitCategoryIds"] = split_category_ids
        existing["splitLines"] = split_lines
        existing["categoryId"] = None
        existing["subcategoryId"] = None
        existing["categorizationStatus"] = CategorizationStatus.MANUALLY_CATEGORIZED.value
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = now

        replaced = await self._repo.replace(transaction_id, existing)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=transaction_id,
            action=AuditAction.SPLIT,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={
                "isSplit": True,
                "splitCount": len(split_lines),
                "splitLines": [
                    {
                        "id": sl["id"],
                        "amount": sl["amount"],
                        "categoryId": sl["categoryId"],
                    }
                    for sl in split_lines
                ],
            },
        )

        return replaced

    async def update_split(
        self,
        transaction_id: str,
        year: int,
        month: int,
        lines: list[dict],
        user_id: str,
        user_name: str,
    ) -> dict:
        """Replace all split lines on an already-split transaction."""
        existing = await self._get_active_transaction(transaction_id, year, month)
        if not existing:
            return None

        if not existing.get("isSplit"):
            raise ValueError("Transaction is not split. Use POST to create a split.")

        parent_amount = Decimal(str(existing["amount"]))
        txn_type = existing.get("transactionType", "expense")

        await self._validate_lines(lines, parent_amount, txn_type)

        old_lines = existing.get("splitLines", [])
        split_lines, split_category_ids = self._build_split_lines(lines, parent_amount)

        now = datetime.now(timezone.utc).isoformat()
        existing["splitCount"] = len(split_lines)
        existing["splitCategoryIds"] = split_category_ids
        existing["splitLines"] = split_lines
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = now

        replaced = await self._repo.replace(transaction_id, existing)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=transaction_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            old_values={
                "splitLines": [
                    {
                        "id": sl["id"],
                        "amount": sl["amount"],
                        "categoryId": sl.get("categoryId"),
                    }
                    for sl in old_lines
                ],
            },
            new_values={
                "splitLines": [
                    {
                        "id": sl["id"],
                        "amount": sl["amount"],
                        "categoryId": sl["categoryId"],
                    }
                    for sl in split_lines
                ],
            },
        )

        return replaced

    async def unsplit_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        user_id: str,
        user_name: str,
    ) -> dict:
        """Remove all split lines and revert to non-split state."""
        existing = await self._get_active_transaction(transaction_id, year, month)
        if not existing:
            return None

        if not existing.get("isSplit"):
            raise ValueError("Transaction is not split.")

        old_lines = existing.get("splitLines", [])

        now = datetime.now(timezone.utc).isoformat()
        existing["isSplit"] = False
        existing["splitCount"] = 0
        existing["splitCategoryIds"] = []
        existing["splitLines"] = []
        existing["categoryId"] = None
        existing["subcategoryId"] = None
        existing["categorizationStatus"] = CategorizationStatus.UNCATEGORIZED.value
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = now

        replaced = await self._repo.replace(transaction_id, existing)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=transaction_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            old_values={
                "isSplit": True,
                "splitLines": [
                    {
                        "id": sl["id"],
                        "amount": sl["amount"],
                        "categoryId": sl.get("categoryId"),
                    }
                    for sl in old_lines
                ],
            },
            new_values={
                "isSplit": False,
                "splitLines": [],
                "categorizationStatus": (CategorizationStatus.UNCATEGORIZED.value),
            },
        )

        return replaced
