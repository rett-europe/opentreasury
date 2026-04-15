from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.models.domain import AuditAction, CategoryType, ReviewStatus, TransactionType


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


def _round_decimal(v):
    if isinstance(v, float):
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return v


# --- Transactions ---


class TransactionCreate(CamelModel):
    transaction_date: date = Field(serialization_alias="date", validation_alias="date")
    value_date: Optional[date] = None
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = "EUR"
    bank_description: Optional[str] = Field(default=None, max_length=500)
    account_id: str
    transaction_type: TransactionType
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: list[str] = []
    detail: Optional[str] = Field(default=None, max_length=2000)
    movement_number: Optional[str] = Field(default=None, max_length=50)
    branch_number: Optional[str] = Field(default=None, max_length=50)
    balance: Optional[Decimal] = Field(default=None, max_digits=14, decimal_places=2)
    source_reference: Optional[str] = Field(default=None, max_length=100)
    counterparty_name: Optional[str] = Field(default=None, max_length=200)
    counterparty_reference: Optional[str] = Field(default=None, max_length=200)
    import_batch_id: Optional[str] = None
    import_source: Optional[str] = None


class TransactionUpdate(CamelModel):
    transaction_date: Optional[date] = Field(default=None, serialization_alias="date", validation_alias="date")
    value_date: Optional[date] = None
    amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    currency: Optional[str] = None
    bank_description: Optional[str] = Field(default=None, max_length=500)
    account_id: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: Optional[list[str]] = None
    detail: Optional[str] = Field(default=None, max_length=2000)
    movement_number: Optional[str] = Field(default=None, max_length=50)
    branch_number: Optional[str] = Field(default=None, max_length=50)
    balance: Optional[Decimal] = Field(default=None, max_digits=14, decimal_places=2)
    source_reference: Optional[str] = Field(default=None, max_length=100)
    counterparty_name: Optional[str] = Field(default=None, max_length=200)
    counterparty_reference: Optional[str] = Field(default=None, max_length=200)
    review_status: Optional[ReviewStatus] = None


# --- Split Lines ---


class SplitLineCreate(CamelModel):
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: list[str] = []
    detail: Optional[str] = Field(default=None, max_length=2000)


class SplitLineResponse(CamelModel):
    id: str
    amount: Decimal
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: list[str] = []
    detail: Optional[str] = None
    sort_order: int = 0

    @field_validator("amount", mode="before")
    @classmethod
    def round_split_amount(cls, v):
        return _round_decimal(v)


class SplitRequest(CamelModel):
    lines: list[SplitLineCreate] = Field(min_length=2, max_length=20)


class TransactionResponse(CamelModel):
    id: str
    transaction_date: date = Field(serialization_alias="date", validation_alias="date")
    value_date: Optional[date] = None
    year: int
    month: int
    partition_key: str
    amount: Decimal
    currency: str = "EUR"
    balance: Optional[Decimal] = None
    movement_number: Optional[str] = None
    branch_number: Optional[str] = None
    bank_description: Optional[str] = None
    account_id: str
    transaction_type: str = "expense"
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    categorization_status: str = "uncategorized"
    tag_ids: list[str] = []
    detail: Optional[str] = None
    source_reference: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_reference: Optional[str] = None
    review_status: str = "pending"
    reviewed_by: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    original_amount: Optional[Decimal] = None
    original_date: Optional[str] = None
    notes: list[dict] = []
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_by_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    is_split: bool = False
    split_count: int = 0
    split_lines: list[SplitLineResponse] = []
    split_category_ids: list[str] = []

    @field_validator("transaction_type", mode="before")
    @classmethod
    def default_transaction_type_from_amount(cls, v, info):
        """Infer transactionType for pre-migration v1 documents."""
        if v is not None:
            return v
        amount = info.data.get("amount")
        if amount is not None and Decimal(str(amount)) > 0:
            return "income"
        return "expense"

    @field_validator("amount", "balance", "original_amount", mode="before")
    @classmethod
    def round_amount(cls, v):
        return _round_decimal(v)


class TransactionListResponse(CamelModel):
    items: list[TransactionResponse]
    continuation_token: Optional[str] = None
    total_income: Optional[Decimal] = None
    total_expenses: Optional[Decimal] = None
    net: Optional[Decimal] = None
    transaction_count: Optional[int] = None
    uncategorized_count: Optional[int] = None

    @field_validator("total_income", "total_expenses", "net", mode="before")
    @classmethod
    def round_aggregate(cls, v):
        return _round_decimal(v)


class ReviewStatusUpdate(CamelModel):
    review_status: ReviewStatus


class CategorizeRequest(CamelModel):
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None


class NoteCreate(CamelModel):
    text: str = Field(max_length=1000)


class NoteResponse(CamelModel):
    id: str
    text: str
    author: str
    author_name: Optional[str] = None
    created_at: datetime


# --- Categories ---


class SubcategoryCreate(CamelModel):
    id: Optional[str] = None
    name: str = Field(max_length=100)


class SubcategoryUpdate(CamelModel):
    name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class SubcategoryResponse(CamelModel):
    id: str
    name: str
    is_active: bool = True


class CategoryCreate(CamelModel):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)
    category_type: CategoryType
    sort_order: int = 0
    subcategories: list[SubcategoryCreate] = []


class CategoryUpdate(CamelModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)
    category_type: Optional[CategoryType] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    subcategories: Optional[list[SubcategoryCreate]] = None


class CategoryResponse(CamelModel):
    id: str
    name: str
    description: Optional[str] = None
    category_type: CategoryType
    sort_order: int = 0
    is_active: bool = True
    subcategories: list[SubcategoryResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Accounts ---


class AccountCreate(CamelModel):
    bank_name: str = Field(max_length=100)
    bank_name_short: Optional[str] = Field(default=None, max_length=50)
    iban: Optional[str] = Field(default=None, max_length=34)
    paypal_email: Optional[str] = Field(default=None, max_length=200)
    account_label: str = Field(max_length=200)
    is_paypal: bool = False
    currency: str = Field(default="EUR", max_length=3)
    sort_order: int = 0


class AccountUpdate(CamelModel):
    bank_name: Optional[str] = Field(default=None, max_length=100)
    bank_name_short: Optional[str] = Field(default=None, max_length=50)
    iban: Optional[str] = Field(default=None, max_length=34)
    paypal_email: Optional[str] = Field(default=None, max_length=200)
    account_label: Optional[str] = Field(default=None, max_length=200)
    is_paypal: Optional[bool] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AccountResponse(CamelModel):
    id: str
    bank_name: str
    bank_name_short: Optional[str] = None
    iban: Optional[str] = None
    paypal_email: Optional[str] = None
    account_label: str
    is_paypal: bool = False
    currency: str = "EUR"
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Tags ---


class TagCreate(CamelModel):
    name: str = Field(max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    sort_order: int = 0


class TagUpdate(CamelModel):
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=20)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TagResponse(CamelModel):
    id: str
    name: str
    color: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Reference Data ---


class ReferenceDataResponse(CamelModel):
    accounts: list[AccountResponse]
    categories: list[CategoryResponse]
    tags: list[TagResponse]


# --- User ---


class UserProfile(CamelModel):
    name: str
    email: str
    role: str


class UserPreferences(CamelModel):
    language: str = "es"
    theme: str = "light"
    compact_mode: bool = False
    reduced_motion: bool = False


# --- Reports ---


class ReportSummary(CamelModel):
    year: int
    total_income: Decimal
    total_expense: Decimal
    net: Decimal

    @field_validator("total_income", "total_expense", "net", mode="before")
    @classmethod
    def round_report_amount(cls, v):
        return _round_decimal(v)


class CategoryBreakdownItem(CamelModel):
    category_id: str
    category_name: Optional[str] = None
    income: Decimal
    expense: Decimal
    net: Decimal

    @field_validator("income", "expense", "net", mode="before")
    @classmethod
    def round_category_amount(cls, v):
        return _round_decimal(v)


class CategoryBreakdown(CamelModel):
    year: int
    month: Optional[int] = None
    items: list[CategoryBreakdownItem]


class MonthlyTrendItem(CamelModel):
    month: int
    income: Decimal
    expense: Decimal
    net: Decimal

    @field_validator("income", "expense", "net", mode="before")
    @classmethod
    def round_trend_amount(cls, v):
        return _round_decimal(v)


class MonthlyTrend(CamelModel):
    year: int
    months: list[MonthlyTrendItem]


class AccountSummaryItem(CamelModel):
    account_id: str
    account_label: Optional[str] = None
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    transaction_count: int

    @field_validator("total_income", "total_expense", "net", mode="before")
    @classmethod
    def round_account_amount(cls, v):
        return _round_decimal(v)


class AccountSummary(CamelModel):
    year: int
    month: Optional[int] = None
    items: list[AccountSummaryItem]


# --- Audit ---


class AuditLogEntry(CamelModel):
    id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    changed_by: str
    changed_by_name: Optional[str] = None
    changed_at: datetime
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None


class AuditListResponse(CamelModel):
    items: list[AuditLogEntry]
    continuation_token: Optional[str] = None


# --- Imports ---


class NewCategoryPreview(CamelModel):
    name: str
    type: str
    suggested_type: str = "expense"


class NewSubcategoryPreview(CamelModel):
    category_name: str
    name: str


class AccountPreview(CamelModel):
    id: str
    label: str
    iban: str


class ImportPreview(CamelModel):
    valid: bool
    import_mode: str = "full"
    errors: list[str] = []
    warnings: list[str] = []
    total_rows: int = 0
    rows_with_errors: int = 0
    account: AccountPreview
    new_categories: list[NewCategoryPreview] = []
    new_subcategories: list[NewSubcategoryPreview] = []
    transactions_to_import: int = 0
    duplicates_to_skip: int = 0


class ExcelImportSummary(CamelModel):
    import_batch_id: str
    import_mode: str
    import_source: str
    account_id: str
    account_label: str
    categories_created: int
    subcategories_added: int
    transactions_imported: int
    duplicates_skipped: int
    rows_skipped: int
    warnings: list[str] = []
