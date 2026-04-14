from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.models.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    SubcategoryCreate,
    SubcategoryUpdate,
)
from app.services.category_service import CategoryService
from app.services.dependencies import (
    get_category_service,
    get_transaction_service,
)
from app.services.transaction_service import TransactionService

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    items = await service.list_categories()
    return [CategoryResponse.model_validate(i) for i in items]


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: CategoryCreate,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    created = await service.create_category(
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    return CategoryResponse.model_validate(created)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
):
    item = await service.get_category(category_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return CategoryResponse.model_validate(item)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
    txn_service: TransactionService = Depends(get_transaction_service),
):
    # Check if any removed subcategories have transactions
    if data.subcategories is not None:
        existing = await service.get_category(category_id)
        if existing:
            new_sub_ids = {s.id for s in data.subcategories if s.id}
            for old_sub in existing.get("subcategories", []):
                old_id = old_sub.get("id")
                if old_id and old_id not in new_sub_ids:
                    count = await txn_service.count_by_subcategory(category_id, old_id)
                    if count > 0:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"Cannot remove subcategory '{old_sub.get('name')}': "
                                f"{count} transaction(s) reference it. Deactivate instead."
                            ),
                        )

    updated = await service.update_category(
        category_id=category_id,
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return CategoryResponse.model_validate(updated)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    try:
        deleted = await service.delete_category(
            category_id, user_id=current_user["oid"], user_name=current_user["name"]
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


@router.post(
    "/{category_id}/subcategories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_subcategory(
    category_id: str,
    data: SubcategoryCreate,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    updated = await service.add_subcategory(
        category_id=category_id,
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return CategoryResponse.model_validate(updated)


@router.put(
    "/{category_id}/subcategories/{subcategory_id}",
    response_model=CategoryResponse,
)
async def update_subcategory(
    category_id: str,
    subcategory_id: str,
    data: SubcategoryUpdate,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    updated = await service.update_subcategory(
        category_id=category_id,
        subcategory_id=subcategory_id,
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category or subcategory not found",
        )
    return CategoryResponse.model_validate(updated)


@router.delete(
    "/{category_id}/subcategories/{subcategory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_subcategory(
    category_id: str,
    subcategory_id: str,
    current_user: dict = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
    txn_service: TransactionService = Depends(get_transaction_service),
):
    count = await txn_service.count_by_subcategory(category_id, subcategory_id)
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Cannot delete subcategory: {count} transaction(s) " "reference it. Deactivate instead."),
        )

    updated = await service.remove_subcategory(
        category_id=category_id,
        subcategory_id=subcategory_id,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category or subcategory not found",
        )
