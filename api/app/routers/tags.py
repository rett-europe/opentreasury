from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.models.schemas import TagCreate, TagResponse, TagUpdate
from app.services.dependencies import get_tag_service
from app.services.tag_service import TagService

router = APIRouter(
    prefix="/api/tags",
    tags=["Tags"],
)


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: dict = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    items = await service.list_tags()
    return [TagResponse.model_validate(i) for i in items]


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    data: TagCreate,
    current_user: dict = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    created = await service.create_tag(
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    return TagResponse.model_validate(created)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    current_user: dict = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    item = await service.get_tag(tag_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return TagResponse.model_validate(item)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    data: TagUpdate,
    current_user: dict = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    updated = await service.update_tag(
        tag_id=tag_id,
        data=data,
        user_id=current_user["oid"],
        user_name=current_user["name"],
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return TagResponse.model_validate(updated)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: dict = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    try:
        deleted = await service.delete_tag(tag_id, user_id=current_user["oid"], user_name=current_user["name"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
