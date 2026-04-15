from decimal import Decimal

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.models.domain import TransactionType
from app.services.cosmos_client import cosmos_service


def _build_filter_conditions(
    partition_key: str,
    filters: dict | None,
    include_deleted: bool,
) -> tuple[list[str], list[dict]]:
    """Build WHERE conditions and parameters shared by list and aggregate queries."""
    conditions = ["c.partitionKey = @pk"]
    parameters: list[dict] = [{"name": "@pk", "value": partition_key}]

    if not include_deleted:
        conditions.append("(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))")

    if filters:
        if "accountId" in filters:
            conditions.append("c.accountId = @accountId")
            parameters.append({"name": "@accountId", "value": filters["accountId"]})
        if "categoryId" in filters:
            conditions.append("c.categoryId = @categoryId")
            parameters.append({"name": "@categoryId", "value": filters["categoryId"]})
        if "subcategoryId" in filters:
            conditions.append("c.subcategoryId = @subcategoryId")
            parameters.append({"name": "@subcategoryId", "value": filters["subcategoryId"]})
        if "tagId" in filters:
            conditions.append("ARRAY_CONTAINS(c.tagIds, @tagId)")
            parameters.append({"name": "@tagId", "value": filters["tagId"]})
        if "search" in filters:
            conditions.append(
                "(CONTAINS(LOWER(c.bankDescription), LOWER(@search))" " OR CONTAINS(LOWER(c.detail), LOWER(@search)))"
            )
            parameters.append({"name": "@search", "value": filters["search"]})
        if "amountMin" in filters:
            conditions.append("c.amount >= @amountMin")
            parameters.append({"name": "@amountMin", "value": filters["amountMin"]})
        if "amountMax" in filters:
            conditions.append("c.amount <= @amountMax")
            parameters.append({"name": "@amountMax", "value": filters["amountMax"]})
        if "transactionType" in filters:
            conditions.append("c.transactionType = @transactionType")
            parameters.append({"name": "@transactionType", "value": filters["transactionType"]})
        if "categorizationStatus" in filters:
            conditions.append("c.categorizationStatus = @categorizationStatus")
            parameters.append(
                {
                    "name": "@categorizationStatus",
                    "value": filters["categorizationStatus"],
                }
            )
        if "reviewStatus" in filters:
            conditions.append("c.reviewStatus = @reviewStatus")
            parameters.append({"name": "@reviewStatus", "value": filters["reviewStatus"]})

    return conditions, parameters


class CosmosTransactionRepository:
    async def list_by_partition(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
        page_size: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        conditions, parameters = _build_filter_conditions(partition_key, filters, include_deleted)

        where = " AND ".join(conditions)
        query = f"SELECT * FROM c WHERE {where} ORDER BY c.date DESC"

        pager = cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
            partition_key=partition_key,
            max_item_count=page_size,
        ).by_page(continuation_token)

        items = []
        async for page in pager:
            items = [item async for item in page]
            break

        return items, pager.continuation_token

    async def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
        try:
            return await cosmos_service.transactions.read_item(item=item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            return None

    async def create(self, document: dict) -> dict:
        return await cosmos_service.transactions.create_item(body=document)

    async def replace(self, item_id: str, document: dict) -> dict:
        return await cosmos_service.transactions.replace_item(item=item_id, body=document)

    async def query_for_report(
        self,
        year: int,
        month: int | None = None,
        account_id: str | None = None,
    ) -> list[dict]:
        if month is not None:
            partition_key = f"{year:04d}-{month:02d}"
            conditions = ["c.partitionKey = @pk"]
            parameters: list[dict] = [{"name": "@pk", "value": partition_key}]
            conditions.append("(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))")
            if account_id:
                conditions.append("c.accountId = @accountId")
                parameters.append({"name": "@accountId", "value": account_id})

            where = " AND ".join(conditions)
            query = (
                "SELECT c.categoryId, c.accountId, c.amount, c.month,"
                " c.transactionType, c.isSplit, c.splitLines"
                f" FROM c WHERE {where}"
            )
            kwargs: dict = {
                "query": query,
                "parameters": parameters,
                "partition_key": partition_key,
            }
        else:
            conditions = ["c.year = @year"]
            parameters = [{"name": "@year", "value": year}]
            conditions.append("(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))")
            if account_id:
                conditions.append("c.accountId = @accountId")
                parameters.append({"name": "@accountId", "value": account_id})

            where = " AND ".join(conditions)
            query = (
                "SELECT c.categoryId, c.accountId, c.amount, c.month,"
                " c.transactionType, c.isSplit, c.splitLines"
                f" FROM c WHERE {where}"
            )
            kwargs = {
                "query": query,
                "parameters": parameters,
            }

        items = []
        async for item in cosmos_service.transactions.query_items(**kwargs):
            items.append(item)
        return items

    async def query_for_export(
        self,
        date_from: str,
        date_to: str,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict]:
        conditions = [
            "c.date >= @dateFrom",
            "c.date <= @dateTo",
            "(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))",
        ]
        parameters: list[dict] = [
            {"name": "@dateFrom", "value": date_from},
            {"name": "@dateTo", "value": date_to},
        ]

        if account_id:
            conditions.append("c.accountId = @accountId")
            parameters.append({"name": "@accountId", "value": account_id})

        if category_id:
            conditions.append("c.categoryId = @categoryId")
            parameters.append({"name": "@categoryId", "value": category_id})

        where = " AND ".join(conditions)
        query = f"SELECT * FROM c WHERE {where} ORDER BY c.date ASC"

        items = []
        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
        ):
            items.append(item)
        return items

    async def count_by_account(self, account_id: str) -> int:
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE c.accountId = @accountId "
            "AND (c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
        )
        parameters = [{"name": "@accountId", "value": account_id}]
        result = 0
        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
        ):
            result += item
        return result

    async def count_by_category(self, category_id: str) -> int:
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE c.categoryId = @categoryId "
            "AND (c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
        )
        parameters = [{"name": "@categoryId", "value": category_id}]
        result = 0
        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
        ):
            result += item
        return result

    async def count_by_subcategory(self, category_id: str, subcategory_id: str) -> int:
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE c.categoryId = @categoryId "
            "AND c.subcategoryId = @subcategoryId "
            "AND (c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
        )
        parameters = [
            {"name": "@categoryId", "value": category_id},
            {"name": "@subcategoryId", "value": subcategory_id},
        ]
        result = 0
        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
        ):
            result += item
        return result

    async def count_by_tag(self, tag_id: str) -> int:
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE ARRAY_CONTAINS(c.tagIds, @tagId) "
            "AND (c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
        )
        parameters = [{"name": "@tagId", "value": tag_id}]
        result = 0
        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
        ):
            result += item
        return result

    async def aggregate_filtered(
        self,
        partition_key: str,
        *,
        filters: dict | None = None,
        include_deleted: bool = False,
    ) -> dict:
        conditions, parameters = _build_filter_conditions(partition_key, filters, include_deleted)
        where = " AND ".join(conditions)
        query = "SELECT c.amount, c.transactionType, c.categoryId, c.isSplit" f" FROM c WHERE {where}"

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        transaction_count = 0
        uncategorized_count = 0

        async for item in cosmos_service.transactions.query_items(
            query=query,
            parameters=parameters,
            partition_key=partition_key,
        ):
            transaction_count += 1
            txn_type = item.get("transactionType")
            amount = abs(Decimal(str(item["amount"])))
            if txn_type == TransactionType.INCOME.value:
                total_income += amount
            elif txn_type == TransactionType.EXPENSE.value:
                total_expenses += amount
            # transfer and refund: excluded from totals
            if not item.get("categoryId") and not item.get("isSplit"):
                uncategorized_count += 1

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "transaction_count": transaction_count,
            "uncategorized_count": uncategorized_count,
        }
