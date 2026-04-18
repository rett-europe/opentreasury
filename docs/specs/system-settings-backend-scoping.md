# System Settings — Backend Scoping (Issue #12)

**Author:** Morpheus (Backend Developer)
**Date:** 2026-04-18
**Branch:** `feature/system-settings-issue-12`
**Status:** Scoping — pending Neo's approval of the alignment delta.

> Companion document to `docs/specs/system-settings-spec.md`. Implements amendments **A1** (server-authoritative `updatedAt`/`updatedBy`) and **A4** (export filenames always ISO).

---

## 1. New Files

| Path | Purpose |
|------|---------|
| `api/app/models/system_settings.py` | Pydantic models (request/response/domain) and enums for currency/dateFormat/numberFormat/defaultLanguage. `extra="forbid"` on the update DTO. |
| `api/app/repositories/cosmos/system_settings_repo.py` | Async Cosmos repository for the singleton `id="system"` document. Methods: `get()`, `upsert(doc)`. |
| `api/app/services/system_settings_service.py` | Business logic: lazy-create defaults on first read; on update, override server-authoritative fields (A1) and persist via repo. |
| `api/app/routers/settings.py` | `GET /api/settings` (any authenticated user) + `PUT /api/settings` (admin only via `Depends(get_current_admin)`). |
| `api/tests/test_system_settings_service.py` | Service-level unit tests (defaults, updates, A1 enforcement, validation). |
| `api/tests/test_router_settings.py` | Router tests (auth gating, A1 client-supplied rejection, enum validation, status codes). |
| `api/tests/test_system_settings_repo.py` (optional) | Round-trip test for the repo (mocked Cosmos client). |

Wire-up edits:
- `api/app/repositories/dependencies.py` — add `get_system_settings_repo()`.
- `api/app/services/dependencies.py` — add `get_system_settings_service()`.
- `api/app/main.py` — include the new router.

---

## 2. Cosmos Container Decision

**Recommendation: reuse the existing `reference_data` container.**

| Option | Pros | Cons |
|--------|------|------|
| Reuse `reference_data` (chosen) | No new infra; partition key already supports a singleton; saves RU floor; matches `accounts`/`tags` precedent | Mixes concern types under one container — manageable via the existing `type` discriminator |
| New container `system_config` | Strict separation of concerns | RU floor cost; Bicep change; teardown/redeploy noise; overkill for one document |

**Document shape:**

```json
{
  "id": "system",
  "type": "system_settings",
  "partitionKey": "system_settings",
  "currency": "EUR",
  "dateFormat": "DD/MM/YYYY",
  "numberFormat": "eu",
  "fiscalYearStartMonth": 1,
  "defaultLanguage": "es",
  "organizationName": "",
  "updatedAt": "2026-04-18T15:00:00Z",
  "updatedBy": "00000000-0000-0000-0000-000000000000",
  "updatedByName": "system"
}
```

The `partitionKey` follows the existing `reference_data` convention (`type`-as-partition). Singleton lookup via point-read on `(id="system", pk="system_settings")` — single RU.

---

## 3. API Contract (Final)

| Method | Path | Auth | Request body | Response body | Status codes |
|--------|------|------|--------------|---------------|--------------|
| `GET` | `/api/settings` | `get_current_user` (any role) | — | `SystemSettingsResponse` | 200 |
| `PUT` | `/api/settings` | `get_current_admin` | `SystemSettingsUpdate` | `SystemSettingsResponse` | 200, 403, 422 |

Notes:
- `SystemSettingsResponse` includes `updatedAt` + `updatedBy` (+ optional `updatedByName`) — both populated by the server (A1).
- `PUT` ignores any client-supplied `updatedAt` / `updatedBy` (Pydantic `extra="forbid"`).
- 403 from `get_current_admin` if a non-admin token reaches PUT.
- 422 on enum / range validation failure.

---

## 4. Pydantic Models (Sketch)

```python
# api/app/models/system_settings.py
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CurrencyCode(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    CHF = "CHF"


class DateFormat(str, Enum):
    DDMMYYYY = "DD/MM/YYYY"
    MMDDYYYY = "MM/DD/YYYY"
    YYYYMMDD = "YYYY-MM-DD"
    DDMMMYYYY = "DD MMM YYYY"


class NumberFormat(str, Enum):
    EU = "eu"  # 1.234,56
    US = "us"  # 1,234.56


class SystemSettingsUpdate(BaseModel):
    """Client-supplied update DTO. Rejects unknown fields (A1)."""
    model_config = ConfigDict(extra="forbid")

    currency: CurrencyCode
    dateFormat: DateFormat
    numberFormat: NumberFormat
    fiscalYearStartMonth: int = Field(ge=1, le=12)
    defaultLanguage: Literal["es", "en"]
    organizationName: str = Field(default="", max_length=80)


class SystemSettingsResponse(SystemSettingsUpdate):
    """Returned by GET and PUT. Includes server-authoritative audit fields."""
    model_config = ConfigDict(extra="ignore")

    updatedAt: datetime
    updatedBy: str
    updatedByName: str = ""


def default_settings() -> dict:
    """Hard-coded defaults used to seed the document on first read."""
    return {
        "id": "system",
        "type": "system_settings",
        "partitionKey": "system_settings",
        "currency": CurrencyCode.EUR.value,
        "dateFormat": DateFormat.DDMMYYYY.value,
        "numberFormat": NumberFormat.EU.value,
        "fiscalYearStartMonth": 1,
        "defaultLanguage": "es",
        "organizationName": "",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "updatedBy": "00000000-0000-0000-0000-000000000000",
        "updatedByName": "system",
    }
```

---

## 5. Admin Guard Status (post `cab41d5`)

After reading `app/services/dependencies.py` and `app/routers/categories.py`:

- The right dependency is **`Depends(get_current_admin)`** from `app.auth.dependencies`. It is the same one used by every existing admin-only mutating endpoint (categories POST/PUT/DELETE, accounts, tags, imports). Pattern is consistent.
- For GET, use `Depends(get_current_user)` — viewers must read currency/date format to render the app.
- No spec change needed. Switch's review confirms the auth refactor is security-positive.

---

## 6. A1 Implementation Approach

The handler chain prevents any client-supplied audit value from leaking through, with **two independent layers of defense**:

1. **Pydantic schema (`SystemSettingsUpdate`) uses `extra="forbid"`** — any request body containing `updatedAt`, `updatedBy`, or any other unknown field is rejected with HTTP 422 *before* the handler runs. This is the primary block.
2. **Service-side override** — the service ignores anything in `data` that isn't a known mutable field and stamps `updated_at` and `updated_by` from server-supplied parameters (the handler passes `current_user["oid"]`, `current_user.get("name", "")`, and `datetime.now(timezone.utc)`). Even if the schema were ever loosened, the service would still overwrite.

Sketch:

```python
# api/app/routers/settings.py
@router.put("", response_model=SystemSettingsResponse)
async def update_settings(
    data: SystemSettingsUpdate,
    current_user: dict = Depends(get_current_admin),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    updated = await service.update(
        data=data,
        updated_by_oid=current_user["oid"],
        updated_by_name=current_user.get("name", ""),
        updated_at_utc=datetime.now(timezone.utc),
    )
    return SystemSettingsResponse.model_validate(updated)
```

---

## 7. Test Plan

**Service-level (`test_system_settings_service.py`):**

- `test_get_returns_defaults_when_document_missing` — lazy seed
- `test_get_persists_defaults_on_first_read` — first GET writes the doc
- `test_update_writes_only_known_fields`
- `test_update_overrides_audit_fields_from_server` (A1)
- `test_default_seed_idempotent` — second GET returns persisted, not re-seeded
- `test_organization_name_trimmed`
- `test_organization_name_truncated_at_80`

**Router-level (`test_router_settings.py`):**

- `test_get_settings_anonymous_returns_401`
- `test_get_settings_viewer_returns_200` (Switch MUST #5)
- `test_get_settings_admin_returns_200`
- `test_put_settings_viewer_returns_403` (Switch MUST #4)
- `test_put_settings_anonymous_returns_401`
- `test_put_settings_admin_returns_200_and_persists`
- `test_put_settings_invalid_currency_returns_422` (Switch MUST #1)
- `test_put_settings_invalid_date_format_returns_422`
- `test_put_settings_invalid_number_format_returns_422`
- `test_put_settings_invalid_fiscal_year_month_returns_422`
- `test_put_settings_invalid_language_returns_422`
- `test_put_settings_organization_name_too_long_returns_422`
- `test_put_settings_client_supplied_updatedby_returns_422` (Switch MUST #2 via `extra="forbid"`)
- `test_put_settings_client_supplied_updatedat_returns_422` (Switch MUST #3 via `extra="forbid"`)
- `test_put_settings_response_includes_server_updatedby_and_updatedat` (A1 verification)
- `test_put_settings_updated_at_within_one_second_of_server_time` (Switch MUST #3)

**Repository (`test_system_settings_repo.py` — optional):**

- `test_repo_get_returns_none_when_missing`
- `test_repo_upsert_round_trip`

---

## 8. Migration / Bootstrap

**Choice: lazy-create on first GET.**

Why over startup seed:
- Startup seeding requires a Cosmos write on every container boot — wasteful and adds boot latency.
- Lazy-create runs at most once per deployment (subsequent GETs hit the persisted doc).
- Aligns with how `reference_data` defaults are already handled.
- Frontend `APP_INITIALIZER` (Trinity §5) calls GET on app boot; the first-ever GET seeds the doc transparently.

Pseudo:

```python
async def get(self) -> dict:
    doc = await self.repo.get()
    if doc is None:
        doc = default_settings()
        await self.repo.upsert(doc)
    return doc
```

---

## 9. Risks / Questions for Neo

1. **`updatedByName` field** — the spec doesn't explicitly require it, but it materially helps the UI's "Last edited by …" display without an extra round trip. Adding it costs nothing but a column. Confirm OK to include.
2. **`extra="forbid"` propagation** — strict validation may bite if Trinity ever sends an extra field by accident during retrofits. I want to keep it strict (security > convenience). Confirm.
3. **Audit log integration** — the existing `AuditService` could record settings changes too. Out of V1 scope per the spec, but easy to add later. Flagged for follow-up.
