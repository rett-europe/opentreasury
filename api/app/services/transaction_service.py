from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.domain import AuditAction, CategorizationStatus, ReviewStatus, TransactionType
from app.models.schemas import TransactionCreate, TransactionUpdate

if TYPE_CHECKING:
    from app.repositories.protocols import CategoryRepository, TransactionRepository
    from app.services.audit_service import AuditService


class TransactionService:
    def __init__(self, *, repo: TransactionRepository, audit_service: AuditService, category_repo: CategoryRepository):
        self._repo = repo
        self._audit = audit_service
        self._category_repo = category_repo

    async def list_transactions(
        self,
        year: int,
        month: int,
        account_id: str | None = None,
        category_id: str | None = None,
        subcategory_id: str | None = None,
        tag_id: str | None = None,
        search: str | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        transaction_type: str | None = None,
        categorization_status: str | None = None,
        review_status: str | None = None,
        include_deleted: bool = False,
        page_size: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None, dict | None]:
        partition_key = f"{year:04d}-{month:02d}"

        filters: dict = {}
        if account_id:
            filters["accountId"] = account_id
        if category_id:
            filters["categoryId"] = category_id
        if subcategory_id:
            filters["subcategoryId"] = subcategory_id
        if tag_id:
            filters["tagId"] = tag_id
        if search:
            filters["search"] = search
        if amount_min is not None:
            filters["amountMin"] = float(amount_min)
        if amount_max is not None:
            filters["amountMax"] = float(amount_max)
        if transaction_type:
            filters["transactionType"] = transaction_type
        if categorization_status:
            filters["categorizationStatus"] = categorization_status
        if review_status:
            filters["reviewStatus"] = review_status

        repo_filters = filters or None

        if continuation_token is None:
            # First page: fetch items and aggregates in parallel
            list_coro = self._repo.list_by_partition(
                partition_key,
                filters=repo_filters,
                include_deleted=include_deleted,
                page_size=page_size,
                continuation_token=None,
            )
            agg_coro = self._repo.aggregate_filtered(
                partition_key,
                filters=repo_filters,
                include_deleted=include_deleted,
            )
            (items, next_token), aggregates = await asyncio.gather(list_coro, agg_coro)
            return items, next_token, aggregates

        # Subsequent pages: no aggregates
        items, next_token = await self._repo.list_by_partition(
            partition_key,
            filters=repo_filters,
            include_deleted=include_deleted,
            page_size=page_size,
            continuation_token=continuation_token,
        )
        return items, next_token, None

    async def get_transaction(self, transaction_id: str, year: int, month: int) -> dict | None:
        partition_key = f"{year:04d}-{month:02d}"
        item = await self._repo.get_by_id(transaction_id, partition_key)
        if not item or item.get("isDeleted"):
            return None
        return item

    @staticmethod
    def _sign_amount(amount: float, transaction_type: str) -> float:
        """AS-001 to AS-004: Sign amount based on transactionType."""
        if transaction_type == TransactionType.INCOME:
            return abs(amount)
        if transaction_type == TransactionType.EXPENSE:
            return -abs(amount)
        # transfer / refund: as-entered
        return amount

    async def _validate_category(
        self,
        category_id: str | None,
        subcategory_id: str | None,
        transaction_type: str,
    ) -> None:
        """Validate CA-002..CA-005. CategoryType is guidance only — no cross-validation."""
        # CA-002: subcategoryId requires categoryId
        if category_id is None:
            if subcategory_id is not None:
                raise ValueError("subcategoryId can only be set when categoryId is also set")
            return

        # CA-003: category must exist and be active
        cat = await self._category_repo.get_by_id(category_id)
        if not cat or not cat.get("isActive", True):
            raise ValueError(f"Category '{category_id}' not found or inactive")

        # CA-004: subcategory must belong to category and be active
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

    async def create_transaction(self, data: TransactionCreate, user_id: str, user_name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        year = data.transaction_date.year
        month = data.transaction_date.month
        partition_key = f"{year:04d}-{month:02d}"
        value_date = data.value_date or data.transaction_date

        # CA / XV validation (before normalization — catches subcategoryId without categoryId)
        await self._validate_category(data.category_id, data.subcategory_id, data.transaction_type)

        # CA-005: null category forces null subcategory
        effective_subcat = data.subcategory_id if data.category_id else None

        # AS-001 to AS-004: sign amount based on transactionType
        signed_amount = self._sign_amount(float(data.amount), data.transaction_type)

        # CS-001, CS-002
        cat_status = (
            CategorizationStatus.MANUALLY_CATEGORIZED if data.category_id else CategorizationStatus.UNCATEGORIZED
        )

        # RS-001: manual → approved; imports (identified by importBatchId) → pending
        review = ReviewStatus.PENDING if data.import_batch_id else ReviewStatus.APPROVED

        doc = {
            "id": str(uuid4()),
            "type": "transaction",
            "partitionKey": partition_key,
            "date": data.transaction_date.isoformat(),
            "valueDate": value_date.isoformat(),
            "year": year,
            "month": month,
            "amount": signed_amount,
            "currency": data.currency,
            "balance": (float(data.balance) if data.balance is not None else None),
            "movementNumber": data.movement_number,
            "branchNumber": data.branch_number,
            "bankDescription": data.bank_description,
            "accountId": data.account_id,
            "transactionType": data.transaction_type.value,
            "categoryId": data.category_id,
            "subcategoryId": effective_subcat,
            "categorizationStatus": cat_status.value,
            "tagIds": data.tag_ids,
            "detail": data.detail,
            "sourceReference": data.source_reference,
            "counterpartyName": data.counterparty_name,
            "counterpartyReference": data.counterparty_reference,
            "importBatchId": data.import_batch_id,
            "importSource": data.import_source,
            "reviewStatus": review.value,
            "reviewedBy": None,
            "reviewedByName": None,
            "reviewedAt": None,
            "originalAmount": None,
            "originalDate": None,
            "notes": [],
            "createdBy": user_id,
            "createdByName": user_name,
            "createdAt": now,
            "updatedBy": None,
            "updatedByName": None,
            "updatedAt": None,
            "isDeleted": False,
        }

        created = await self._repo.create(doc)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=created["id"],
            action=AuditAction.CREATE,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={
                "amount": signed_amount,
                "transactionType": data.transaction_type.value,
                "accountId": data.account_id,
                "categoryId": data.category_id,
            },
        )

        return created

    async def update_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        data: TransactionUpdate,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_transaction(transaction_id, year, month)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()
        old_values: dict = {}
        new_values: dict = {}
        updates = data.model_dump(exclude_unset=True)

        def _track(field: str, old_val, new_val):
            if old_val != new_val:
                old_values[field] = old_val
                new_values[field] = new_val

        # TC-001: Preserve original amount on first edit
        if "amount" in updates and existing.get("originalAmount") is None:
            existing["originalAmount"] = existing["amount"]

        # TC-002: Preserve original date on first edit
        if "transaction_date" in updates and existing.get("originalDate") is None:
            existing["originalDate"] = existing.get("date")

        # --- Simple field updates ---
        _simple = {
            "currency": "currency",
            "bank_description": "bankDescription",
            "account_id": "accountId",
            "detail": "detail",
            "movement_number": "movementNumber",
            "branch_number": "branchNumber",
            "source_reference": "sourceReference",
            "counterparty_name": "counterpartyName",
            "counterparty_reference": "counterpartyReference",
        }
        for py_key, doc_key in _simple.items():
            if py_key in updates:
                val = updates[py_key]
                _track(doc_key, existing.get(doc_key), val)
                existing[doc_key] = val

        # Date
        if data.transaction_date is not None:
            new_date = data.transaction_date.isoformat()
            _track("date", existing.get("date"), new_date)
            existing["date"] = new_date
            existing["year"] = data.transaction_date.year
            existing["month"] = data.transaction_date.month
            existing["partitionKey"] = f"{data.transaction_date.year:04d}-{data.transaction_date.month:02d}"

        if data.value_date is not None:
            existing["valueDate"] = data.value_date.isoformat()

        # Balance
        if data.balance is not None:
            existing["balance"] = float(data.balance)

        # Tag IDs
        if data.tag_ids is not None:
            _track("tagIds", existing.get("tagIds"), data.tag_ids)
            existing["tagIds"] = data.tag_ids

        # Transaction type
        if data.transaction_type is not None:
            new_type = data.transaction_type.value
            _track("transactionType", existing.get("transactionType"), new_type)
            existing["transactionType"] = new_type

        # --- Category handling (CA-001 to CA-005) ---
        cat_explicitly_set = "category_id" in updates
        subcat_explicitly_set = "subcategory_id" in updates

        if cat_explicitly_set:
            new_cat = data.category_id
            _track("categoryId", existing.get("categoryId"), new_cat)
            existing["categoryId"] = new_cat

            # CA-005: null categoryId forces subcategoryId null
            if new_cat is None:
                _track("subcategoryId", existing.get("subcategoryId"), None)
                existing["subcategoryId"] = None
            elif subcat_explicitly_set:
                _track("subcategoryId", existing.get("subcategoryId"), data.subcategory_id)
                existing["subcategoryId"] = data.subcategory_id
        elif subcat_explicitly_set:
            _track("subcategoryId", existing.get("subcategoryId"), data.subcategory_id)
            existing["subcategoryId"] = data.subcategory_id

        # Effective values for validation
        eff_type = existing.get("transactionType")
        eff_cat_id = existing.get("categoryId")
        eff_subcat_id = existing.get("subcategoryId")

        # CA / XV validation
        await self._validate_category(eff_cat_id, eff_subcat_id, eff_type)

        # AS-005, AS-006: Re-sign amount when transactionType or amount changes
        if data.amount is not None or data.transaction_type is not None:
            raw = float(data.amount) if data.amount is not None else existing.get("amount", 0)
            signed = self._sign_amount(raw, eff_type)
            _track("amount", existing.get("amount"), signed)
            existing["amount"] = signed

        # CS-003 to CS-005: Update categorization status
        if cat_explicitly_set:
            if existing.get("categoryId") is None:
                new_cs = CategorizationStatus.UNCATEGORIZED.value
            else:
                new_cs = CategorizationStatus.MANUALLY_CATEGORIZED.value
            _track("categorizationStatus", existing.get("categorizationStatus"), new_cs)
            existing["categorizationStatus"] = new_cs

        # Review status
        if data.review_status is not None:
            new_rs = data.review_status.value
            _track("reviewStatus", existing.get("reviewStatus"), new_rs)
            existing["reviewStatus"] = new_rs
            existing["reviewedBy"] = user_id
            existing["reviewedByName"] = user_name
            existing["reviewedAt"] = now

        # Metadata
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = now

        replaced = await self._repo.replace(transaction_id, existing)

        if old_values:
            await self._audit.log(
                entity_type="Transaction",
                entity_id=transaction_id,
                action=AuditAction.UPDATE,
                changed_by=user_id,
                changed_by_name=user_name,
                old_values=old_values,
                new_values=new_values,
            )

        return replaced

    async def soft_delete_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        user_id: str,
        user_name: str,
    ) -> bool:
        existing = await self.get_transaction(transaction_id, year, month)
        if not existing:
            return False

        existing["isDeleted"] = True
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        await self._repo.replace(transaction_id, existing)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=transaction_id,
            action=AuditAction.DELETE,
            changed_by=user_id,
            changed_by_name=user_name,
            old_values={"isDeleted": False},
            new_values={"isDeleted": True},
        )

        return True

    async def review_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        review_status: ReviewStatus,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_transaction(transaction_id, year, month)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()
        old_status = existing.get("reviewStatus")
        existing["reviewStatus"] = review_status.value
        existing["reviewedBy"] = user_id
        existing["reviewedByName"] = user_name
        existing["reviewedAt"] = now
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
            old_values={"reviewStatus": old_status},
            new_values={"reviewStatus": review_status.value},
        )

        return replaced

    async def categorize_transaction(
        self,
        transaction_id: str,
        year: int,
        month: int,
        category_id: str | None,
        subcategory_id: str | None,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_transaction(transaction_id, year, month)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()
        eff_type = existing.get("transactionType")

        # CA-005: null category forces null subcategory
        if category_id is None:
            subcategory_id = None

        # Validate
        await self._validate_category(category_id, subcategory_id, eff_type)

        old_values = {
            "categoryId": existing.get("categoryId"),
            "subcategoryId": existing.get("subcategoryId"),
            "categorizationStatus": existing.get("categorizationStatus"),
        }

        existing["categoryId"] = category_id
        existing["subcategoryId"] = subcategory_id
        existing["categorizationStatus"] = (
            CategorizationStatus.MANUALLY_CATEGORIZED.value if category_id else CategorizationStatus.UNCATEGORIZED.value
        )
        existing["updatedBy"] = user_id
        existing["updatedByName"] = user_name
        existing["updatedAt"] = now

        new_values = {
            "categoryId": category_id,
            "subcategoryId": subcategory_id,
            "categorizationStatus": existing["categorizationStatus"],
        }

        replaced = await self._repo.replace(transaction_id, existing)

        await self._audit.log(
            entity_type="Transaction",
            entity_id=transaction_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            old_values=old_values,
            new_values=new_values,
        )

        return replaced

    async def bulk_categorize(
        self,
        items: list[dict],
        action: str,
        category_id: str | None,
        subcategory_id: str | None,
        user_id: str,
        user_name: str,
    ) -> tuple[str, list[str], list[dict]]:
        """Apply or clear category+subcategory on a batch of transactions.

        Per spec `docs/specs/bulk-category-update-spec.md` v1.1 (§15 / A-1..A-4, AC-24):
          - action == "apply":   set categoryId + optional subcategoryId,
                                 categorizationStatus = manually_categorized.
          - action == "clear":   set categoryId = subcategoryId = null,
                                 categorizationStatus = uncategorized.

        Request-level validation (raises ValueError -> 422 in the router):
          - action == "apply" requires a valid, active categoryId and, if given,
            a valid active subcategoryId under that category.

        Per-row outcomes are returned in (succeeded, failed) with stable error codes:
          - NOT_FOUND                       -- transaction missing or soft-deleted
          - SPLIT_PARENT_NOT_BULK_UPDATABLE -- transaction has isSplit == True
          - CONCURRENCY_CONFLICT            -- repo.replace raised

        One audit entry is written per affected row, all sharing the same
        batchCorrelationId (returned to the caller).
        """
        action_norm = action.lower() if isinstance(action, str) else action
        if action_norm not in ("apply", "clear"):
            raise ValueError("action must be 'apply' or 'clear'")

        if action_norm == "clear":
            category_id = None
            subcategory_id = None

        # Request-level category validation (apply mode only). Failures here
        # fail the whole request with HTTP 422 — per spec §15 / A-2.
        if action_norm == "apply":
            # Pass any transaction_type; _validate_category uses it only for
            # CategoryType guidance which it no longer enforces.
            await self._validate_category(category_id, subcategory_id, TransactionType.EXPENSE.value)

        batch_correlation_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        if action_norm == "apply":
            new_status = CategorizationStatus.MANUALLY_CATEGORIZED.value
        else:
            new_status = CategorizationStatus.UNCATEGORIZED.value

        succeeded: list[str] = []
        failed: list[dict] = []

        for item in items:
            tx_id = item["id"]
            year = item["year"]
            month = item["month"]
            partition_key = f"{year:04d}-{month:02d}"

            existing = await self._repo.get_by_id(tx_id, partition_key)
            if not existing or existing.get("isDeleted"):
                failed.append(
                    {
                        "id": tx_id,
                        "code": "NOT_FOUND",
                        "message": "Transaction not found",
                    }
                )
                continue

            # AC-24: split parents must be rejected in bulk even if selected.
            if existing.get("isSplit"):
                failed.append(
                    {
                        "id": tx_id,
                        "code": "SPLIT_PARENT_NOT_BULK_UPDATABLE",
                        "message": "Split transactions cannot be bulk re-categorized",
                    }
                )
                continue

            old_values = {
                "categoryId": existing.get("categoryId"),
                "subcategoryId": existing.get("subcategoryId"),
                "categorizationStatus": existing.get("categorizationStatus"),
            }

            existing["categoryId"] = category_id
            existing["subcategoryId"] = subcategory_id
            existing["categorizationStatus"] = new_status
            existing["updatedBy"] = user_id
            existing["updatedByName"] = user_name
            existing["updatedAt"] = now

            new_values = {
                "categoryId": category_id,
                "subcategoryId": subcategory_id,
                "categorizationStatus": new_status,
            }

            try:
                await self._repo.replace(tx_id, existing)
            except Exception as exc:  # noqa: BLE001 -- surfaced as per-row CONCURRENCY_CONFLICT
                failed.append(
                    {
                        "id": tx_id,
                        "code": "CONCURRENCY_CONFLICT",
                        "message": str(exc) or "Concurrency conflict while updating transaction",
                    }
                )
                continue

            await self._audit.log(
                entity_type="Transaction",
                entity_id=tx_id,
                action=AuditAction.UPDATE,
                changed_by=user_id,
                changed_by_name=user_name,
                old_values=old_values,
                new_values=new_values,
                batch_correlation_id=batch_correlation_id,
            )
            succeeded.append(tx_id)

        return batch_correlation_id, succeeded, failed

    async def add_note(
        self,
        transaction_id: str,
        year: int,
        month: int,
        text: str,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_transaction(transaction_id, year, month)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()
        note = {
            "id": str(uuid4()),
            "text": text,
            "author": user_id,
            "authorName": user_name,
            "createdAt": now,
        }

        notes = existing.get("notes", [])
        notes.append(note)
        existing["notes"] = notes
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
            new_values={"note_added": note["id"]},
        )

        return replaced

    async def get_transactions_for_report(
        self,
        year: int,
        month: int | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
        return await self._repo.query_for_report(year, month, account_id)

    async def get_transactions_for_export(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict]:
        return await self._repo.query_for_export(date_from, date_to, account_id, category_id)

    async def count_by_account(self, account_id: str) -> int:
        return await self._repo.count_by_account(account_id)

    async def count_by_category(self, category_id: str) -> int:
        return await self._repo.count_by_category(category_id)

    async def count_by_subcategory(self, category_id: str, subcategory_id: str) -> int:
        return await self._repo.count_by_subcategory(category_id, subcategory_id)

    async def count_by_tag(self, tag_id: str) -> int:
        return await self._repo.count_by_tag(tag_id)
