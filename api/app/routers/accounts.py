from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.models.schemas import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService
from app.services.dependencies import (
    get_account_service,
    get_transaction_service,
)
from app.services.transaction_service import TransactionService

router = APIRouter(
    prefix="/api/accounts",
    tags=["Accounts"],
)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    current_user: dict = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
):
    items = await service.list_accounts()
    return [AccountResponse.model_validate(i) for i in items]


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    data: AccountCreate,
    current_user: dict = Depends(get_current_admin),
    service: AccountService = Depends(get_account_service),
):
    created = await service.create_account(
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    return AccountResponse.model_validate(created)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
):
    item = await service.get_account(account_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return AccountResponse.model_validate(item)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    data: AccountUpdate,
    current_user: dict = Depends(get_current_admin),
    service: AccountService = Depends(get_account_service),
):
    updated = await service.update_account(
        account_id=account_id,
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return AccountResponse.model_validate(updated)


@router.get("/{account_id}/transaction-count")
async def get_account_transaction_count(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
    txn_service: TransactionService = Depends(get_transaction_service),
):
    item = await service.get_account(account_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    count = await txn_service.count_by_account(account_id)
    return {"count": count}


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    current_user: dict = Depends(get_current_admin),
    service: AccountService = Depends(get_account_service),
):
    try:
        deleted = await service.delete_account(account_id, user_id=current_user["oid"], user_name=current_user["name"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
