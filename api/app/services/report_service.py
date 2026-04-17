from __future__ import annotations

import logging
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

from app.models.domain import TransactionType

logger = logging.getLogger("opentreasury")

_INCOME = TransactionType.INCOME.value
_EXPENSE = TransactionType.EXPENSE.value
_INCOME_EXPENSE = {_INCOME, _EXPENSE}

if TYPE_CHECKING:
    from app.services.category_service import CategoryService
    from app.services.transaction_service import TransactionService


class ReportService:
    def __init__(self, *, transaction_service: TransactionService, category_service: CategoryService):
        self._txn = transaction_service
        self._cat = category_service

    async def get_summary(self, year: int) -> dict:
        items = await self._txn.get_transactions_for_report(year=year)

        total_income = Decimal("0")
        total_expense = Decimal("0")

        for item in items:
            txn_type = item.get("transactionType")
            if txn_type == _INCOME:
                total_income += abs(Decimal(str(item["amount"])))
            elif txn_type == _EXPENSE:
                total_expense += abs(Decimal(str(item["amount"])))
            # transfer and refund: excluded from income/expense totals

        return {
            "year": year,
            "total_income": total_income,
            "total_expense": total_expense,
            "net": total_income - total_expense,
        }

    async def get_by_category(self, year: int, month: int | None = None) -> dict:
        items = await self._txn.get_transactions_for_report(year=year, month=month)

        buckets: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
        for item in items:
            txn_type = item.get("transactionType")
            if txn_type not in _INCOME_EXPENSE:
                continue  # transfer and refund: excluded from category breakdown

            if item.get("isSplit") and item.get("splitLines"):
                # Aggregate at split-line level
                for line in item["splitLines"]:
                    cat = line.get("categoryId") or "uncategorized"
                    amount = abs(Decimal(str(line["amount"])))
                    if txn_type == _INCOME:
                        buckets[cat]["income"] += amount
                    else:
                        buckets[cat]["expense"] += amount
            else:
                cat = item.get("categoryId") or "uncategorized"
                amount = abs(Decimal(str(item["amount"])))
                if txn_type == _INCOME:
                    buckets[cat]["income"] += amount
                else:
                    buckets[cat]["expense"] += amount

        breakdown_items = [
            {
                "category_id": cat_id,
                "income": data["income"],
                "expense": data["expense"],
                "net": data["income"] - data["expense"],
            }
            for cat_id, data in buckets.items()
        ]

        return {"year": year, "month": month, "items": breakdown_items}

    async def get_balance(self, year: int) -> dict:
        items = await self._txn.get_transactions_for_report(year=year)

        # Get all categories for name lookup
        categories = await self._cat.list_categories()
        category_map = {cat["id"]: cat["name"] for cat in categories}
        subcategory_map = {}
        for cat in categories:
            for sub in cat.get("subcategories", []):
                subcategory_map[sub["id"]] = sub["name"]

        buckets: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

        for item in items:
            txn_type = item.get("transactionType")
            if txn_type not in _INCOME_EXPENSE:
                continue  # transfer and refund: excluded from balance

            if item.get("isSplit") and item.get("splitLines"):
                # Aggregate at split-line level
                for line in item["splitLines"]:
                    cat_id = line.get("categoryId") or "uncategorized"
                    subcat_id = line.get("subcategoryId")
                    key = f"{cat_id}:{subcat_id}" if subcat_id else cat_id
                    amount = abs(Decimal(str(line["amount"])))
                    if txn_type == _INCOME:
                        buckets[key]["income"] += amount
                    else:
                        buckets[key]["expense"] += amount
            else:
                cat_id = item.get("categoryId") or "uncategorized"
                subcat_id = item.get("subcategoryId")
                key = f"{cat_id}:{subcat_id}" if subcat_id else cat_id
                amount = abs(Decimal(str(item["amount"])))
                if txn_type == _INCOME:
                    buckets[key]["income"] += amount
                else:
                    buckets[key]["expense"] += amount

        balance_items = []
        for key, data in buckets.items():
            if ":" in key:
                cat_id, subcat_id = key.split(":", 1)
            else:
                cat_id = key
                subcat_id = None

            category_name = category_map.get(cat_id)
            if category_name is None:
                logger.warning("Category '%s' not found in reference data — falling back to 'Uncategorized'", cat_id)
                category_name = "Uncategorized"

            balance_items.append(
                {
                    "category_id": cat_id,
                    "category_name": category_name,
                    "subcategory_id": subcat_id,
                    "subcategory_name": subcategory_map.get(subcat_id, "") if subcat_id else None,
                    "income": data["income"],
                    "expense": data["expense"],
                    "net": data["income"] - data["expense"],
                }
            )

        return {"year": year, "items": balance_items}

    async def get_monthly_trend(self, year: int) -> dict:
        items = await self._txn.get_transactions_for_report(year=year)

        monthly: dict[int, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

        for item in items:
            txn_type = item.get("transactionType")
            if txn_type not in _INCOME_EXPENSE:
                continue  # transfer and refund: excluded from monthly totals
            m = item["month"]
            amount = abs(Decimal(str(item["amount"])))
            if txn_type == _INCOME:
                monthly[m]["income"] += amount
            else:
                monthly[m]["expense"] += amount

        months = []
        for m in sorted(monthly.keys()):
            inc = monthly[m]["income"]
            exp = monthly[m]["expense"]
            months.append({"month": m, "income": inc, "expense": exp, "net": inc - exp})

        return {"year": year, "months": months}

    async def get_by_account(self, year: int, month: int | None = None) -> dict:
        items = await self._txn.get_transactions_for_report(year=year, month=month)

        buckets: dict[str, dict] = defaultdict(
            lambda: {
                "income": Decimal("0"),
                "expense": Decimal("0"),
                "count": 0,
            }
        )

        for item in items:
            acc = item.get("accountId", "unknown")
            buckets[acc]["count"] += 1  # count ALL types including transfers/refunds
            txn_type = item.get("transactionType")
            if txn_type == _INCOME:
                buckets[acc]["income"] += abs(Decimal(str(item["amount"])))
            elif txn_type == _EXPENSE:
                buckets[acc]["expense"] += abs(Decimal(str(item["amount"])))
            # transfer and refund: excluded from income/expense totals

        account_items = [
            {
                "account_id": acc_id,
                "total_income": data["income"],
                "total_expense": data["expense"],
                "net": data["income"] - data["expense"],
                "transaction_count": data["count"],
            }
            for acc_id, data in buckets.items()
        ]

        return {"year": year, "month": month, "items": account_items}
