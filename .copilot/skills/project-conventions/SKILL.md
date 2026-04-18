---
name: "project-conventions"
description: "Enforceable engineering conventions for the NGO Treasury backend (Python FastAPI + Cosmos DB)"
domain: "project-conventions"
confidence: "high"
source: "codebase-audit-2026-04-12"
---

## Context

NGO Treasury is a FastAPI backend with Cosmos DB NoSQL (serverless), serving an Angular frontend authenticated via Microsoft Entra ID (rett.es tenant). The API manages bank transactions, categories, accounts, tags, and audit trails for a small Spanish NGO (~200-500 transactions/year).

**Tech stack:** Python 3.12+, FastAPI, Pydantic v2, azure-cosmos async SDK, openpyxl (imports/exports), python-jose (JWT), httpx, gunicorn + uvicorn workers.

**Read this skill BEFORE writing any code.** These conventions are enforced — violations will be caught in review.

---

## 1. Architecture & Layering

The codebase uses three layers. Respect their boundaries.

```
Router (HTTP) → Service (business logic) → Repository (data access)
```

### Router Layer (`app/routers/`)

Routers are **thin HTTP controllers**. They:
- Parse and validate request parameters (via Pydantic + FastAPI Query/Body)
- Check auth (`Depends(get_current_user)` or `Depends(get_current_admin)`)
- Call ONE service method
- Map service results to HTTP responses (status codes, response models)
- Raise `HTTPException` for error cases

Routers **MUST NOT**:
- Contain business logic (aggregation, calculations, conditional workflows)
- Call repositories directly
- Call multiple services in sequence to compose a result (that's a service's job)
- Perform audit logging (the service handles it)

**✅ CORRECT — thin router:**
```python
# app/routers/accounts.py
@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    current_user: dict = Depends(get_current_admin),
    service: AccountService = Depends(get_account_service),
):
    created = await service.create_account(
        data=data, user_id=current_user["oid"], user_name=current_user["name"]
    )
    return AccountResponse.model_validate(created)
```

**❌ WRONG — business logic in router:**
```python
# DO NOT do report aggregation in routers
@router.get("/summary")
async def get_summary(year: int, service: TransactionService = Depends(...)):
    items = await service.get_transactions_for_report(year=year)
    total_income = Decimal("0")
    for item in items:
        amount = Decimal(str(item["amount"]))
        if amount > 0:
            total_income += amount  # This belongs in a ReportService
```

**❌ WRONG — audit logging in router:**
```python
# DO NOT call audit_svc directly from a router
@router.delete("/{account_id}")
async def delete_account(..., audit_svc: AuditService = Depends(get_audit_service)):
    await service.delete_account(account_id)
    await audit_svc.log(...)  # This belongs inside AccountService.delete_account()
```

### Service Layer (`app/services/`)

Services contain **all business logic**. They:
- Accept repositories via constructor injection
- Validate business rules (e.g., "cannot delete category if transactions reference it")
- Construct Cosmos documents from Pydantic models
- Call audit service for all CUD operations
- Return plain `dict` documents (Cosmos-native format)

Services **MUST NOT**:
- Import or use `cosmos_service` directly
- Construct SQL/NoSQL query strings
- Know about HTTP status codes or `HTTPException`
- Import from `fastapi`

**✅ CORRECT — service with injected repo:**
```python
class AccountService:
    def __init__(self, *, repo: ReferenceItemRepository, audit_service: AuditService):
        self._repo = repo
        self._audit = audit_service

    async def create_account(self, data: AccountCreate, user_id: str, user_name: str) -> dict:
        doc = { ... }
        created = await self._repo.create(doc, _PARTITION_KEY)
        await self._audit.log(entity_type="BankAccount", entity_id=acc_id, ...)
        return created
```

### Repository Layer (`app/repositories/`)

Repositories handle **all Cosmos DB interaction**. They:
- Implement Protocol interfaces defined in `app/repositories/protocols.py`
- Live in `app/repositories/cosmos/` (one file per repo)
- Construct parameterized queries (NEVER string interpolation)
- Access Cosmos containers via the `cosmos_service` singleton

Repositories **MUST NOT**:
- Contain business logic
- Import Pydantic schemas
- Know about user identity or audit

**Protocol pattern (interface):**
```python
# app/repositories/protocols.py
class CategoryRepository(Protocol):
    async def list_all(self) -> list[dict]: ...
    async def get_by_id(self, category_id: str) -> dict | None: ...
    async def create(self, document: dict) -> dict: ...
    async def replace(self, category_id: str, document: dict) -> dict: ...
    async def delete(self, category_id: str) -> None: ...
```

**Cosmos implementation:**
```python
# app/repositories/cosmos/category_repo.py
from app.services.cosmos_client import cosmos_service

class CosmosCategoryRepository:
    async def list_all(self) -> list[dict]:
        query = "SELECT * FROM c ORDER BY c.sortOrder ASC"
        items = []
        async for item in cosmos_service.categories.query_items(query=query):
            items.append(item)
        return items
```

**Always use parameterized queries:**
```python
# ✅ CORRECT — parameterized
query = "SELECT * FROM c WHERE c.accountId = @accountId"
parameters = [{"name": "@accountId", "value": account_id}]

# ❌ WRONG — string interpolation (SQL injection risk)
query = f"SELECT * FROM c WHERE c.accountId = '{account_id}'"
```

---

## 2. File Organization

### Directory Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── config.py                # Environment settings (pydantic-settings)
│   ├── main.py                  # FastAPI app, lifespan, middleware, router includes
│   ├── auth/
│   │   ├── __init__.py
│   │   └── dependencies.py      # JWT validation, get_current_user, get_current_admin
│   ├── constants/               # ← NEW: domain constants go here
│   │   ├── __init__.py
│   │   └── import_constants.py  # HEADER_ALIASES, REQUIRED_HEADERS, etc.
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── error_handler.py     # Cosmos exception → HTTP response mapping
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py            # Enums (AuditAction, CategoryType)
│   │   └── schemas.py           # Pydantic request/response models (will be split per-domain)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── protocols.py         # Protocol interfaces for ALL repos
│   │   ├── dependencies.py      # Singleton repo instances + getter functions
│   │   └── cosmos/              # Cosmos DB implementations
│   │       ├── __init__.py
│   │       ├── transaction_repo.py
│   │       ├── category_repo.py
│   │       ├── reference_item_repo.py
│   │       ├── audit_repo.py
│   │       └── user_preferences_repo.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   ├── accounts.py
│   │   ├── tags.py
│   │   ├── reports.py
│   │   ├── export.py
│   │   ├── imports.py
│   │   ├── reference_data.py
│   │   ├── user.py
│   │   └── audit.py
│   └── services/
│       ├── __init__.py
│       ├── dependencies.py       # FastAPI Depends() wiring for all services
│       ├── cosmos_client.py      # CosmosService singleton (DB init/close)
│       ├── account_service.py
│       ├── category_service.py
│       ├── transaction_service.py
│       ├── import_service.py
│       ├── export_service.py
│       ├── audit_service.py
│       ├── tag_service.py
│       ├── report_service.py     # ← NEW: report aggregation logic
│       └── reference_data_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures, mocks, factories
│   ├── fixtures/                 # Test data files (xlsx, etc.)
│   ├── test_{service}_service.py # Service unit tests
│   ├── test_router_{name}.py     # Router integration tests
│   └── test_{topic}.py           # Other tests (auth, error_handler, etc.)
└── requirements.in               # Direct dependencies (pip-compile input)
```

### Where Constants Live

| Constant type | Location | Example |
|---|---|---|
| Environment config | `app/config.py` (Settings class) | `COSMOS_ENDPOINT`, `CORS_ORIGINS` |
| Domain enums | `app/models/domain.py` | `CategoryType`, `AuditAction`, `TransactionType` |
| Enum value aliases for comparisons | Top of the consuming file | `_INCOME = TransactionType.INCOME.value` |
| Import-specific aliases | `app/constants/import_constants.py` | `HEADER_ALIASES`, `REQUIRED_HEADERS` |
| Service-internal partition keys | Top of the service file | `_PARTITION_KEY = "bank_account"` |
| Audit TTL | `app/config.py` or `app/constants/` | `AUDIT_TTL_SECONDS = 220752000` |

**❌ WRONG — large constant dicts hardcoded in service files:**
```python
# DO NOT put this in import_service.py
HEADER_ALIASES: dict[str, list[str]] = {
    "date": ["fecha", "date", "data", "datum"],
    # ... 15 more entries
}
```

**✅ CORRECT — extract to constants module:**
```python
# app/constants/import_constants.py
HEADER_ALIASES: dict[str, list[str]] = { ... }
REQUIRED_HEADERS = {"date", "amount", "category", "subcategory"}
INCOME_ALIASES = {"entrada", "income", "receita", ...}
EXPENSE_ALIASES = {"gasto", "expense", "despesa", ...}

# app/services/import_service.py
from app.constants.import_constants import HEADER_ALIASES, REQUIRED_HEADERS, ...
```

---

## 3. Code Style

### Python Conventions

- **Python version:** 3.12+ (use `X | Y` union syntax, not `Union[X, Y]`)
- **Naming:** `snake_case` for functions, variables, modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level constants
- **Line length:** 120 characters max
- **Formatter:** `black --line-length=120`
- **Linter:** `flake8 --max-line-length=120 --exclude=__pycache__`
- **Imports:** Use `from __future__ import annotations` in files with forward references. Use `if TYPE_CHECKING:` for type hints that would cause circular imports.

### Mandatory Pre-Commit Checks

**Every agent MUST run these before reporting work as done:**
```bash
cd api
flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__
black --check app/ tests/ --line-length=120
pytest tests/ -v --override-ini="addopts="
```

These run on ALL files, not just changed files. Pre-existing lint errors are your responsibility.

### Type Hints

- All function signatures MUST have type hints (parameters + return type)
- Use `dict` not `Dict`, `list` not `List`, `X | None` not `Optional[X]` (Python 3.12+)
- Exception: `Optional` from `typing` is acceptable in Pydantic models for clarity

```python
# ✅ CORRECT
async def get_account(self, account_id: str) -> dict | None:

# ❌ WRONG — missing return type
async def get_account(self, account_id: str):
```

### Enum Values — Never Hardcode Domain Strings

When comparing against domain values (transaction types, categorization statuses, review statuses, audit actions), **always use the enum from `app/models/domain.py`**, never hardcoded strings. This prevents silent breakage if enum values change and makes refactoring safe.

```python
from app.models.domain import TransactionType

# ✅ CORRECT — use enum values
_INCOME = TransactionType.INCOME.value
_EXPENSE = TransactionType.EXPENSE.value
_INCOME_EXPENSE = (_INCOME, _EXPENSE)

if txn_type == _INCOME:
    total_income += amount
elif txn_type == _EXPENSE:
    total_expense += amount

if txn_type not in _INCOME_EXPENSE:
    continue

# ❌ WRONG — hardcoded strings
if txn_type == "income":     # Magic string — breaks silently if enum changes
    total_income += amount
```

For files that check enum values frequently (e.g., `report_service.py`), define module-level aliases at the top:

```python
_INCOME = TransactionType.INCOME.value
_EXPENSE = TransactionType.EXPENSE.value
_INCOME_EXPENSE = (_INCOME, _EXPENSE)
```

For files with only 1-2 comparisons, inline is fine: `TransactionType.INCOME.value`.

### Import Ordering

Standard library → third-party → local app modules. Within each group, alphabetical.

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin, get_current_user
from app.models.schemas import TransactionCreate, TransactionResponse
from app.services.dependencies import get_transaction_service
```

---

## 4. Pydantic Models (`app/models/`)

### Base Model

All API-facing models extend `CamelModel` for automatic camelCase serialization:

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

### Model Naming Convention

| Suffix | Purpose | Example |
|---|---|---|
| `Create` | Request body for POST | `TransactionCreate` |
| `Update` | Request body for PUT/PATCH (all fields Optional) | `TransactionUpdate` |
| `Response` | API response shape | `TransactionResponse` |
| `ListResponse` | Paginated list with continuation token | `TransactionListResponse` |

### Decimal Handling

Always use `Decimal` for monetary values, never `float`. Apply `quantize` on input:

```python
from decimal import Decimal, ROUND_HALF_UP

def _round_decimal(v):
    if isinstance(v, float):
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return v
```

### Current State: Monolithic `schemas.py`

Currently ALL schemas (~490 lines) live in one file. When splitting (see cleanup backlog), organize as:
```
models/
├── domain.py             # Enums only
├── schemas/
│   ├── __init__.py       # Re-export all schemas for backward compatibility
│   ├── base.py           # CamelModel, _round_decimal
│   ├── transactions.py
│   ├── categories.py
│   ├── accounts.py
│   ├── tags.py
│   ├── reports.py
│   ├── users.py
│   └── imports.py
```

---

## 5. Dependency Injection

### Pattern

FastAPI `Depends()` wires everything. Two DI files:

1. **`repositories/dependencies.py`** — creates singleton repo instances, exposes getter functions
2. **`services/dependencies.py`** — composes services from repos + other services, using `Depends()`

```python
# repositories/dependencies.py
_transaction_repo = CosmosTransactionRepository()

def get_transaction_repo() -> CosmosTransactionRepository:
    return _transaction_repo

# services/dependencies.py
def get_transaction_service(
    repo=Depends(get_transaction_repo),
    audit_service: AuditService = Depends(get_audit_service),
    category_repo=Depends(get_category_repo),
) -> TransactionService:
    return TransactionService(repo=repo, audit_service=audit_service, category_repo=category_repo)
```

### Service Constructor Pattern

Services take dependencies as **keyword-only arguments**:

```python
class TransactionService:
    def __init__(self, *, repo: TransactionRepository, audit_service: AuditService, category_repo: CategoryRepository):
        self._repo = repo
        self._audit = audit_service
        self._category_repo = category_repo
```

This makes testing trivial — inject `AsyncMock()` objects.

### Anti-Pattern: Injecting Multiple Unrelated Services in a Router

```python
# ❌ WRONG — router orchestrates service calls
@router.delete("/{id}")
async def delete_account(
    service: AccountService = Depends(...),
    txn_service: TransactionService = Depends(...),
    audit_svc: AuditService = Depends(...),
):
    count = await txn_service.count_by_account(id)  # Cross-service call in router
    if count > 0: raise HTTPException(409, ...)
    await service.delete_account(id)
    await audit_svc.log(...)  # Manual audit in router

# ✅ CORRECT — service encapsulates the logic
@router.delete("/{id}")
async def delete_account(
    service: AccountService = Depends(...),
):
    await service.delete_account(id)  # Service handles ref check + audit
```

---

## 6. Error Handling

### HTTP Status Codes

| Situation | Code | Detail |
|---|---|---|
| Resource not found | `404` | `"Transaction not found"` |
| Auth missing/invalid | `401` | `"Invalid token header"` |
| Insufficient permissions | `403` | `"Admin access required"` |
| Validation error | `422` | (automatic from Pydantic) |
| Referential integrity violation | `409` | `"Cannot delete account: N transaction(s) reference it"` |
| File too large | `413` | `"File too large. Maximum size is 10 MB"` |
| Wrong content type | `415` | `"Expected an .xlsx file"` |
| Cosmos rate limiting | `429` | `"Too many requests, please retry later"` |
| Cosmos generic error | `502` | `"Database operation failed"` |
| Unhandled exception | `500` | `"Internal server error"` |

### Error Response Format

All errors use FastAPI's standard `{"detail": "message"}` format. Do NOT invent custom error shapes.

### Exception Hierarchy

- **`ValueError`** — raised by services for invalid input (caught by router)
- **`HTTPException`** — raised by routers only, NEVER in services
- **Cosmos exceptions** — caught globally by `middleware/error_handler.py`
- **Unhandled** — caught by the generic handler, logged, returns 500

```python
# ✅ Service raises ValueError
class ImportService:
    async def import_workbook(self, data: bytes, ...) -> dict:
        if not data:
            raise ValueError("No movement sheet found in workbook")

# ✅ Router converts to HTTPException
@router.post("/import")
async def import_file(...):
    try:
        result = await service.import_workbook(body, ...)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

---

## 7. Testing

### Framework & Runner

- **Framework:** pytest (with pytest-asyncio for async tests)
- **Run:** `cd api && pytest tests/ -v --override-ini="addopts="`
- **Location:** `api/tests/`

### Test File Naming

| Test type | File pattern | Example |
|---|---|---|
| Service unit test | `test_{name}_service.py` | `test_transaction_service.py` |
| Router integration test | `test_router_{name}.py` | `test_router_transactions.py` |
| Other | `test_{topic}.py` | `test_auth.py`, `test_error_handler.py` |

### What Must Be Tested

Every service MUST have a corresponding `test_{name}_service.py` file testing:
- All public methods
- Happy path + edge cases
- Error cases (not found, invalid input, reference violations)

Every router MUST have a corresponding `test_router_{name}.py` file testing:
- All endpoints (GET, POST, PUT, DELETE)
- Auth enforcement (both user and admin roles)
- 404/409/422 error cases

### Mocking Pattern (Service Tests)

Services are tested with `AsyncMock` repositories:

```python
@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def mock_audit():
    return AsyncMock()

@pytest.fixture
def service(mock_repo, mock_audit):
    return AccountService(repo=mock_repo, audit_service=mock_audit)

async def test_create_account(service, mock_repo, mock_audit):
    mock_repo.create.return_value = {"id": "acc-123", ...}
    result = await service.create_account(data=..., user_id="u1", user_name="User")
    mock_repo.create.assert_called_once()
    mock_audit.log.assert_called_once()
```

### Router Tests (httpx AsyncClient)

Router tests use `httpx.AsyncClient` with the FastAPI app, overriding DI:

```python
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
async def client(mock_service, admin_token):
    app.dependency_overrides[get_transaction_service] = lambda: mock_service
    app.dependency_overrides[get_current_admin] = lambda: admin_token
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

### Test Fixtures

- Excel test workbooks live in `tests/fixtures/`
- Use factory functions in `conftest.py` for document creation: `make_transaction()`, `make_category()`, `make_audit_entry()`
- Set environment variables BEFORE any app import (see top of `conftest.py`)

---

## 8. Database Access (Cosmos DB)

### Container Layout

| Container | Partition key | Stores |
|---|---|---|
| `transactions` | `/partitionKey` ("YYYY-MM") | Transaction documents |
| `categories` | `/id` | Category documents (with embedded subcategories) |
| `reference_data` | `/type` | Accounts ("bank_account"), Tags ("tag"), UserPreferences ("user_preferences") |
| `audit_log` | `/entityType` | Audit trail entries (TTL: 7 years) |

### Partition Key Format

Transactions use synthetic partition key: `f"{year:04d}-{month:02d}"` (e.g., "2026-04").

### Query Patterns

Always use parameterized queries. Build conditions list + parameters list, then join:

```python
conditions = ["c.partitionKey = @pk"]
parameters = [{"name": "@pk", "value": partition_key}]

if not include_deleted:
    conditions.append("(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))")

if account_id:
    conditions.append("c.accountId = @accountId")
    parameters.append({"name": "@accountId", "value": account_id})

where = " AND ".join(conditions)
query = f"SELECT * FROM c WHERE {where} ORDER BY c.date DESC"
```

### Cosmos Client Singleton

`CosmosService` in `app/services/cosmos_client.py` manages the async Cosmos client lifecycle. Initialized in the FastAPI `lifespan` context manager. Repos access containers via `cosmos_service.transactions`, `cosmos_service.categories`, etc.

---

## 9. Authentication & Authorization

### Two Auth Levels

| Dependency | Who | Used for |
|---|---|---|
| `get_current_user` | Any authenticated rett.es user | Read endpoints |
| `get_current_admin` | Users with "Admin" app role | Write endpoints (create, update, delete) |

### JWT Validation

- Tokens from Microsoft Entra ID (v1 and v2 supported)
- JWKS fetched and cached (1 hour TTL)
- Both `api://{client_id}` and raw `{client_id}` audiences accepted
- Both v1 (`sts.windows.net`) and v2 (`login.microsoftonline.com`) issuers accepted

### User Claims Format

Services receive `user_id` (OID) and `user_name` (display name) as separate parameters, NOT the raw JWT dict.

---

## 10. Anti-Patterns to Avoid

### ❌ Business Logic in Routers

The `reports.py` router currently contains all report aggregation logic (Decimal arithmetic, defaultdict bucketing, trend calculation). This MUST be extracted to a `ReportService`.

### ❌ Audit Logging in Routers

The `accounts.py` `delete_account` endpoint calls `audit_svc.log()` directly from the router. Audit logging for all CUD operations MUST happen inside the service.

### ❌ Large Constant Dicts in Service Files

`import_service.py` contains ~30 lines of `HEADER_ALIASES`, `REQUIRED_HEADERS`, `INCOME_ALIASES`, `EXPENSE_ALIASES` at the top of the file. Extract to `app/constants/import_constants.py`.

### ❌ Missing Protocol for UserPreferencesRepository

`CosmosUserPreferencesRepository` exists but has no Protocol in `protocols.py`. Every repo must have a Protocol.

### ❌ Catching Bare `Exception`

```python
# ❌ In Cosmos repos
async def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
    try:
        return await cosmos_service.transactions.read_item(...)
    except Exception:  # Too broad — catches KeyboardInterrupt, SystemExit, etc.
        return None

# ✅ CORRECT — catch the specific Cosmos exception
from azure.cosmos.exceptions import CosmosResourceNotFoundError

async def get_by_id(self, item_id: str, partition_key: str) -> dict | None:
    try:
        return await cosmos_service.transactions.read_item(...)
    except CosmosResourceNotFoundError:
        return None
```

### ❌ Exporting IDs Instead of Display Names

`export_service.py` writes `accountId`, `categoryId`, `subcategoryId` to the Excel export. Users see UUIDs instead of "Unicaja", "Subvenciones", etc. The export should resolve IDs to display names.

### ❌ Hardcoded Domain String Comparisons

Comparing against raw strings like `"income"`, `"expense"`, `"pending"`, `"approved"` instead of using enum values from `app/models/domain.py`. This was caught in the split transactions PR — `report_service.py` had 11 occurrences of `== "income"` / `== "expense"` that should have been `TransactionType.INCOME.value` / `TransactionType.EXPENSE.value`. If an enum value ever changes, hardcoded strings break silently.

```python
# ❌ WRONG — magic strings
if txn_type == "income":
    total_income += amount

# ✅ CORRECT — enum values
from app.models.domain import TransactionType
if txn_type == TransactionType.INCOME.value:
    total_income += amount
```

### ❌ Hardcoded Spanish Column Headers in Export

`export_service.py` has hardcoded Spanish headers: `"Fecha"`, `"Observaciones"`, `"Categoría"`, `"Importe"`. These should be constants, consistent with the multilingual approach used in imports.

---

## 11. Document Conventions

### Cosmos Document Fields

All documents use camelCase keys (matching the Azure Cosmos SDK convention and the Angular frontend):

```python
doc = {
    "id": str(uuid4()),
    "type": "transaction",
    "partitionKey": "2026-04",
    "date": "2026-04-10",
    "createdBy": user_id,
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "isDeleted": False,
}
```

### Timestamps

Always UTC, ISO 8601 format: `datetime.now(timezone.utc).isoformat()`

### IDs

- Transactions: `str(uuid4())` (full UUID)
- Accounts: `f"acc-{uuid4().hex[:12]}"`
- Tags: `f"tag-{uuid4().hex[:12]}"`
- Categories: `str(uuid4())`
- Subcategories: `str(uuid4())` (embedded in parent category)

### Soft Delete

Transactions use soft delete (`isDeleted: true`). All other entity types use physical delete (with referential integrity checks first).

---

## 12. API URL Conventions

- All endpoints prefixed with `/api/`
- Resource names are plural, lowercase: `/api/transactions`, `/api/categories`, `/api/accounts`, `/api/tags`
- Sub-resources use nesting: `/api/categories/{id}/subcategories`
- Reports: `/api/reports/summary`, `/api/reports/by-category`, `/api/reports/monthly-trend`, `/api/reports/by-account`
- Actions: `/api/imports/preview`, `/api/imports/unicaja-template`
- Health: `/api/health`

---

## Quick Reference

| What | Where | Command |
|---|---|---|
| Lint | `cd api` | `flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__` |
| Format check | `cd api` | `black --check app/ tests/ --line-length=120` |
| Format fix | `cd api` | `black app/ tests/ --line-length=120` |
| Tests | `cd api` | `pytest tests/ -v --override-ini="addopts="` |
| Start server | `cd api` | `uvicorn app.main:app --reload --port 8000` |
| Dependencies | `cd api` | `pip-compile requirements.in` then `pip install -r requirements.txt` |
```

## Anti-Patterns

<!-- List things to avoid in this codebase -->
- **[Anti-pattern]** — Explanation of what not to do and why.
