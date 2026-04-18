import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.auth.dependencies import get_current_admin
from app.models.domain import TransactionType
from app.models.schemas import ExcelImportSummary, ImportPreview
from app.services.dependencies import get_import_service
from app.services.import_service import ImportService

router = APIRouter(
    prefix="/api/imports",
    tags=["Imports"],
)

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


async def _read_upload(file: UploadFile) -> bytes:
    """Read and validate an uploaded file."""
    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request body is empty")
    if len(body) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )
    return body


@router.post("/preview", response_model=ImportPreview)
async def preview_import(
    file: UploadFile = File(...),
    account_id: str = Query(..., alias="accountId", min_length=1),
    sheet: Optional[str] = Query(None, min_length=1, max_length=200),
    current_user: dict = Depends(get_current_admin),
    service: ImportService = Depends(get_import_service),
):
    body = await _read_upload(file)

    try:
        preview = await service.preview_workbook(body, account_id=account_id, sheet=sheet)
    except ValueError as exc:
        detail = str(exc)
        if "not found or inactive" in detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

    return ImportPreview.model_validate(preview)


@router.post("/workbook", response_model=ExcelImportSummary, status_code=status.HTTP_201_CREATED)
async def import_workbook(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    account_id: str = Query(..., alias="accountId", min_length=1),
    sheet: Optional[str] = Query(None, min_length=1, max_length=200),
    current_user: dict = Depends(get_current_admin),
    service: ImportService = Depends(get_import_service),
):
    body = await _read_upload(file)

    category_type_overrides: dict[str, str] = {}
    if metadata:
        try:
            parsed = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="metadata must be valid JSON",
            ) from exc
        category_type_overrides = parsed.get("categoryTypeOverrides", {})
        for name, value in category_type_overrides.items():
            if value not in (TransactionType.INCOME.value, TransactionType.EXPENSE.value):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category type '{value}' for '{name}'. Must be 'income' or 'expense'.",
                )

    try:
        summary = await service.import_workbook(
            body,
            account_id=account_id,
            category_type_overrides=category_type_overrides,
            user_id=current_user["oid"],
            user_name=current_user["name"],
            sheet=sheet,
        )
    except ValueError as exc:
        detail = str(exc)
        if "not found or inactive" in detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc

    return ExcelImportSummary.model_validate(summary)
