from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_admin
from app.models.schemas import SplitRequest, TransactionResponse
from app.services.dependencies import get_split_service
from app.services.split_service import SplitService

router = APIRouter(
    prefix="/api/transactions",
    tags=["Split Transactions"],
)


@router.post(
    "/{transaction_id}/split",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_split(
    transaction_id: str,
    data: SplitRequest,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: SplitService = Depends(get_split_service),
):
    try:
        lines = [line.model_dump(by_alias=True) for line in data.lines]
        result = await service.split_transaction(
            transaction_id=transaction_id,
            year=year,
            month=month,
            lines=lines,
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


@router.put(
    "/{transaction_id}/split",
    response_model=TransactionResponse,
)
async def update_split(
    transaction_id: str,
    data: SplitRequest,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: SplitService = Depends(get_split_service),
):
    try:
        lines = [line.model_dump(by_alias=True) for line in data.lines]
        result = await service.update_split(
            transaction_id=transaction_id,
            year=year,
            month=month,
            lines=lines,
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


@router.delete(
    "/{transaction_id}/split",
    response_model=TransactionResponse,
)
async def delete_split(
    transaction_id: str,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: dict = Depends(get_current_admin),
    service: SplitService = Depends(get_split_service),
):
    try:
        result = await service.unsplit_transaction(
            transaction_id=transaction_id,
            year=year,
            month=month,
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
