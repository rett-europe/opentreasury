from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.schemas import (
    AccountResponse,
    CategoryResponse,
    ReferenceDataResponse,
    TagResponse,
)
from app.services.dependencies import get_reference_data_service
from app.services.reference_data_service import ReferenceDataService

router = APIRouter(
    prefix="/api/reference-data",
    tags=["Reference Data"],
)


@router.get("", response_model=ReferenceDataResponse)
async def get_reference_data(
    current_user: dict = Depends(get_current_user),
    service: ReferenceDataService = Depends(get_reference_data_service),
):
    data = await service.get_all()
    return ReferenceDataResponse(
        accounts=[AccountResponse.model_validate(a) for a in data["accounts"]],
        categories=[CategoryResponse.model_validate(c) for c in data["categories"]],
        tags=[TagResponse.model_validate(t) for t in data["tags"]],
    )
