from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.auth.dependencies import get_current_user
from app.services.dependencies import get_export_service
from app.services.export_service import ExportService

router = APIRouter(
    prefix="/api/export",
    tags=["Export"],
)


@router.get("/transactions")
async def export_transactions(
    date_from: date = Query(..., alias="dateFrom"),
    date_to: date = Query(..., alias="dateTo"),
    account_id: str | None = Query(None, alias="accountId"),
    category_id: str | None = Query(None, alias="categoryId"),
    current_user: dict = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    xlsx_bytes = await service.export_transactions_xlsx(
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        category_id=category_id,
    )

    filename = f"movimientos_{date_from.isoformat()}_{date_to.isoformat()}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type=("application/vnd.openxmlformats-officedocument" ".spreadsheetml.sheet"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
