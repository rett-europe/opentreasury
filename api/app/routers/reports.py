from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.models.schemas import (
    AccountSummary,
    AccountSummaryItem,
    BalanceBreakdown,
    BalanceItem,
    CategoryBreakdown,
    CategoryBreakdownItem,
    MonthlyTrend,
    MonthlyTrendItem,
    ReportSummary,
)
from app.services.dependencies import get_report_service
from app.services.report_service import ReportService

# Report read queries are not audited to avoid noise — only write operations
# are audited.  All endpoints here are GET-only aggregations.
router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


@router.get("/summary", response_model=ReportSummary)
async def get_summary(
    year: int = Query(..., ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    result = await service.get_summary(year=year)
    return ReportSummary(
        year=result["year"],
        total_income=result["total_income"],
        total_expense=result["total_expense"],
        net=result["net"],
    )


@router.get("/by-category", response_model=CategoryBreakdown)
async def get_by_category(
    year: int = Query(..., ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    result = await service.get_by_category(year=year, month=month)
    breakdown_items = [
        CategoryBreakdownItem(
            category_id=item["category_id"],
            income=item["income"],
            expense=item["expense"],
            net=item["net"],
        )
        for item in result["items"]
    ]
    return CategoryBreakdown(year=result["year"], month=result["month"], items=breakdown_items)


@router.get("/balance", response_model=BalanceBreakdown)
async def get_balance(
    year: int = Query(..., ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    result = await service.get_balance(year=year)
    balance_items = [
        BalanceItem(
            category_id=item["category_id"],
            category_name=item["category_name"],
            subcategory_id=item.get("subcategory_id"),
            subcategory_name=item.get("subcategory_name"),
            income=item["income"],
            expense=item["expense"],
            net=item["net"],
        )
        for item in result["items"]
    ]
    return BalanceBreakdown(year=result["year"], items=balance_items)


@router.get("/monthly-trend", response_model=MonthlyTrend)
async def get_monthly_trend(
    year: int = Query(..., ge=2020, le=2100),
    current_user: dict = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    result = await service.get_monthly_trend(year=year)
    months = [
        MonthlyTrendItem(month=m["month"], income=m["income"], expense=m["expense"], net=m["net"])
        for m in result["months"]
    ]
    return MonthlyTrend(year=result["year"], months=months)


@router.get("/by-account", response_model=AccountSummary)
async def get_by_account(
    year: int = Query(..., ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    result = await service.get_by_account(year=year, month=month)
    account_items = [
        AccountSummaryItem(
            account_id=item["account_id"],
            total_income=item["total_income"],
            total_expense=item["total_expense"],
            net=item["net"],
            transaction_count=item["transaction_count"],
        )
        for item in result["items"]
    ]
    return AccountSummary(year=result["year"], month=result["month"], items=account_items)
