from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_admin
from app.models.schemas import AuditListResponse, AuditLogEntry
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"],
)


@router.get("", response_model=AuditListResponse)
async def get_audit_trail(
    entity_type: str | None = Query(None, alias="entityType"),
    entity_id: str | None = Query(None, alias="entityId"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    continuation_token: str | None = Query(None, alias="continuationToken"),
    current_user: dict = Depends(get_current_admin),
    service: AuditService = Depends(get_audit_service),
):
    items, next_token = await service.query_trail(
        entity_type=entity_type,
        entity_id=entity_id,
        page_size=page_size,
        continuation_token=continuation_token,
    )
    return AuditListResponse(
        items=[AuditLogEntry.model_validate(i) for i in items],
        continuation_token=next_token,
    )
