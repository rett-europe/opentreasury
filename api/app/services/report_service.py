from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.transaction_service import TransactionService


class ReportService:
    def __init__(self, *, transaction_service: TransactionService):
        self._txn = transaction_service

    async def get_summary(self, year: int) -> dict:
        items = await self._txn.get_transactions_for_report(year=year)

        total_income = Decimal("0")
        total_expense = Decimal("0")

        for item in items:
            txn_type = item.get("transactionType")
            if txn_type == "income":
                total_income += abs(Decimal(str(item["amount"])))
            elif txn_type == "expense":
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
            if txn_type not in ("income", "expense"):
                continue  # transfer and refund: excluded from category breakdown
            cat = item.get("categoryId") or "uncategorized"
            amount = abs(Decimal(str(item["amount"])))
            if txn_type == "income":
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

    async def get_monthly_trend(self, year: int) -> dict:
        items = await self._txn.get_transactions_for_report(year=year)

        monthly: dict[int, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

        for item in items:
            txn_type = item.get("transactionType")
            if txn_type not in ("income", "expense"):
                continue  # transfer and refund: excluded from monthly totals
            m = item["month"]
            amount = abs(Decimal(str(item["amount"])))
            if txn_type == "income":
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
            if txn_type == "income":
                buckets[acc]["income"] += abs(Decimal(str(item["amount"])))
            elif txn_type == "expense":
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
