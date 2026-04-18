from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.models.domain import CategorizationStatus, ReviewStatus, TransactionType
from app.models.schemas import (
    CategorizeRequest,
    NoteCreate,
    ReviewStatusUpdate,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.dependencies import get_transaction_service
from app.services.transaction_service import TransactionService

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    account_id: str | None = Query(None, alias="accountId"),
    category_id: str | None = Query(None, alias="categoryId"),
    subcategory_id: str | None = Query(None, alias="subcategoryId"),
    tag_id: str | None = Query(None, alias="tagId"),
    search: str | None = Query(None, max_length=200),
    amount_min: Decimal | None = Query(None, alias="amountMin"),
    amount_max: Decimal | None = Query(None, alias="amountMax"),
    transaction_type: TransactionType | None = Query(None, alias="transactionType"),
    categorization_status: CategorizationStatus | None = Query(None, alias="categorizationStatus"),
    review_status_filter: ReviewStatus | None = Query(None, alias="reviewStatus"),
    include_deleted: bool = Query(False, alias="includeDeleted"),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    continuation_token: str | None = Query(None, alias="continuationToken"),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
):
    # Only admins may see deleted transactions
    if include_deleted and current_user["role"] != "Admin":
        include_deleted = False

    items, next_token, aggregates = await service.list_transactions(
        year=year,
        month=month,
        account_id=account_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
        tag_id=tag_id,
        search=search,
        amount_min=amount_min,
        amount_max=amount_max,
        transaction_type=transaction_type.value if transaction_type else None,
        categorization_status=categorization_status.value if categorization_status else None,
        review_status=review_status_filter.value if review_status_filter else None,
        include_deleted=include_deleted,
        page_size=page_size,
        continuation_token=continuation_token,
    )
    response = TransactionListResponse(
        items=[TransactionResponse.model_validate(i) for i in items],
        continuation_token=next_token,
    )
    if aggregates:
        response.total_income = aggregates["total_income"]
        response.total_expenses = aggregates["total_expenses"]
        response.net = aggregates["net"]
        response.transaction_count = aggregates["transaction_count"]
        response.uncategorized_count = aggregates["uncategorized_count"]
    return response


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    data: TransactionCreate,
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        created = await service.create_transaction(
            data=data,
            user_id=current_user["oid"],
            user_name=current_user["name"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    return TransactionResponse.model_validate(created)


@router.get("/uncategorized", response_model=TransactionListResponse)
async def list_uncategorized_transactions(
    account_id: str | None = Query(None, alias="accountId"),
    page_size: int = Query(100, ge=1, le=200, alias="pageSize"),
    continuation_token: str | None = Query(None, alias="continuationToken"),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
):
    """List all uncategorized, non-deleted transactions across partitions.

    Cross-partition Cosmos DB query — intentional admin workflow for categorizing
    imported transactions without a date range restriction. Paginated.
    """
    items, next_token = await service.list_uncategorized(
        account_id=account_id,
        page_size=page_size,
        continuation_token=continuation_token,
    )
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(i) for i in items],
        continuation_token=next_token,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
):
    item = await service.get_transaction(transaction_id=transaction_id, year=year, month=month)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse.model_validate(item)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        updated = await service.update_transaction(
            transaction_id=transaction_id,
            year=year,
            month=month,
            data=data,
            user_id=current_user["oid"],
            user_name=current_user["name"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse.model_validate(updated)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    deleted = await service.soft_delete_transaction(
        transaction_id=transaction_id,
        year=year,
        month=month,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )


@router.patch("/{transaction_id}/review", response_model=TransactionResponse)
async def review_transaction(
    transaction_id: str,
    data: ReviewStatusUpdate,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    result = await service.review_transaction(
        transaction_id=transaction_id,
        year=year,
        month=month,
        review_status=data.review_status,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse.model_validate(result)


@router.patch("/{transaction_id}/categorize", response_model=TransactionResponse)
async def categorize_transaction(
    transaction_id: str,
    data: CategorizeRequest,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        result = await service.categorize_transaction(
            transaction_id=transaction_id,
            year=year,
            month=month,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            user_id=current_user["oid"],
            user_name=current_user["name"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse.model_validate(result)


@router.post(
    "/{transaction_id}/notes",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_note(
    transaction_id: str,
    data: NoteCreate,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: TransactionService = Depends(get_transaction_service),
):
    result = await service.add_note(
        transaction_id=transaction_id,
        year=year,
        month=month,
        text=data.text,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return TransactionResponse.model_validate(result)
