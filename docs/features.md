# OpenTreasury — Feature Catalog

A financial management platform built for non-governmental organizations. It tracks bank accounts, categorizes income and expenses, supports multilingual Excel imports, and provides reporting tools for annual financial oversight. Designed for small-to-medium NGO teams with an Admin/Viewer role model.

**Audience:** Developers, contributors, and stakeholders.
**Source of truth:** The code. This document describes *what* — for *how*, follow the source links.

---

## Table of Contents

- [Authentication & Authorization](#authentication--authorization)
- [Dashboard](#dashboard)
- [Transactions](#transactions)
- [Accounts](#accounts)
- [Categories](#categories)
- [Tags](#tags)
- [Reports](#reports)
- [Export](#export)
- [Import](#import)
- [Reference Data](#reference-data)
- [Audit Trail](#audit-trail)
- [App Settings](#app-settings)
- [Health Check](#health-check)
- [Platform](#platform)

---

## Authentication & Authorization

Single-tenant Azure AD (Entra ID) authentication with JWT validation. All routes require authentication.

| Aspect | Detail |
|--------|--------|
| **Provider** | Azure AD (Entra ID), single-tenant |
| **Token format** | JWT — supports v1 and v2 token formats |
| **Roles** | **Admin** (full CRUD) · **Viewer** (read-only + export) |
| **Frontend guard** | `MsalGuard` on all routes; `adminGuard` redirects Viewers away from write operations |
| **Backend enforcement** | `get_current_admin` (write endpoints) · `get_current_user` (read endpoints) |

**Source:** [api/app/auth/](../api/app/auth/) · [frontend/src/app/core/guards/](../frontend/src/app/core/guards/)

---

## Dashboard

Annual financial overview — the landing page after login.

- Displays income, expenses, and net balance by month for the selected year.
- Shows current account balances.
- Endpoint: `GET /api/reports/summary`

**Access:** All users.

**Source:** [frontend/src/app/features/dashboard/](../frontend/src/app/features/dashboard/) · [api/app/routers/reports.py](../api/app/routers/reports.py)

---

## Transactions

Core entity — records of financial movements tied to accounts, categories, and tags.

| Aspect | Detail |
|--------|--------|
| **Operations** | Create, read, update, soft-delete |
| **Partition key** | `YYYY-MM` (year-month of transaction date) |
| **Filters** | Account, category, subcategory, tag, free-text search, amount range |
| **Pagination** | Cosmos DB continuation token |
| **Amount signing** | Automatic — positive for income categories, negative for expense categories |
| **Access** | Read: all users · Write/delete: Admin only |

**Key fields:** `id`, `date`, `valueDate`, `amount` (signed), `currency`, `balance`, `movementNumber`, `accountId`, `categoryId`, `subcategoryId`, `tagIds[]`, `detail`, `isDeleted`.

**Source:** [api/app/routers/transactions.py](../api/app/routers/transactions.py) · [api/app/services/transaction_service.py](../api/app/services/transaction_service.py)

---

## Accounts

Bank account management. Supports traditional (IBAN) and PayPal accounts.

| Aspect | Detail |
|--------|--------|
| **Operations** | Create, read, update, deactivate |
| **Types** | IBAN-based bank accounts · PayPal |
| **Active/Inactive toggle** | Requires confirmation showing transaction count |
| **Deletion constraint** | Cannot delete if transactions exist — returns `409 Conflict`. Deactivate instead. |
| **Access** | Read: all users · Write: Admin only |

**Source:** [api/app/routers/accounts.py](../api/app/routers/accounts.py) · [api/app/services/account_service.py](../api/app/services/account_service.py)

---

## Categories

Hierarchical income/expense classification with nested subcategories.

| Aspect | Detail |
|--------|--------|
| **Structure** | Category → Subcategory (one-to-many) |
| **Types** | `income` or `expense` — locked after creation |
| **Referential integrity** | Cannot delete categories or subcategories that have transactions. Cannot remove a subcategory from a category if transactions reference it. Deactivate instead. |
| **Access** | Read: all users · Write: Admin only |

**Source:** [api/app/routers/categories.py](../api/app/routers/categories.py) · [api/app/services/category_service.py](../api/app/services/category_service.py)

---

## Tags

Color-coded labels with many-to-many relationship to transactions.

| Aspect | Detail |
|--------|--------|
| **Fields** | Name, color, sort order, active/inactive |
| **Deletion constraint** | Cannot delete tags in use by transactions — returns `409 Conflict` |
| **Access** | Read: all users · Write: Admin only |

**Source:** [api/app/routers/tags.py](../api/app/routers/tags.py) · [api/app/services/tag_service.py](../api/app/services/tag_service.py)

---

## Reports

Four pre-built report types for financial analysis. All read-only, all users.

| Report | What it shows |
|--------|---------------|
| **Summary** | Annual income, expenses, net balance by month |
| **By Category** | Totals grouped by category and subcategory |
| **Monthly Trend** | 12-month rolling trend of income vs. expenses |
| **By Account** | Totals per bank account |

**Source:** [api/app/routers/reports.py](../api/app/routers/reports.py) · [frontend/src/app/features/reports/](../frontend/src/app/features/reports/)

---

## Export

XLSX download of transaction data.

| Aspect | Detail |
|--------|--------|
| **Format** | Excel (.xlsx), 13 columns |
| **Filters** | Date range (required), optional account and category filters |
| **Access** | All users (Viewers included) |

**Source:** [api/app/routers/export.py](../api/app/routers/export.py) · [api/app/services/export_service.py](../api/app/services/export_service.py)

---

## Import

Multilingual Excel import with a strict two-step validation flow. **[Full documentation →](features/import.md)**

| Aspect | Detail |
|--------|--------|
| **Flow** | Preview (dry-run validation gate) → Confirm (execute import) |
| **Languages** | Headers recognized in ES, EN, PT, FR, DE |
| **Validation** | Data integrity, subcategory completeness, duplicate detection — all checked before import |
| **Category sync** | Creates missing categories/subcategories from a dedicated sheet (additive only) |
| **Duplicate detection** | Composite key: `date + movementNumber + description + detail + amount` |
| **File limit** | 10 MB, `.xlsx` only |
| **Access** | Admin only |

**Source:** [api/app/services/import_service.py](../api/app/services/import_service.py) · [frontend/src/app/features/import/](../frontend/src/app/features/import/)

---

## Reference Data

Bulk endpoint returning all accounts, categories, and tags in a single call.

- Endpoint: `GET /api/reference-data`
- Frontend caches the response and invalidates after any mutation to accounts, categories, or tags.
- Reduces chattiness on initial load and after CRUD operations.

**Source:** [api/app/routers/reference_data.py](../api/app/routers/reference_data.py) · [api/app/services/reference_data_service.py](../api/app/services/reference_data_service.py)

---

## Audit Trail

Every admin write operation is logged with before/after values.

| Aspect | Detail |
|--------|--------|
| **What's logged** | Entity type, entity ID, action, old values, new values, user, timestamp |
| **Query** | By entity type, entity ID |
| **Access** | Admin only (API) |
| **Limitation** | No UI yet — API-only |

**Source:** [api/app/routers/audit.py](../api/app/routers/audit.py) · [api/app/services/audit_service.py](../api/app/services/audit_service.py)

---

## App Settings

User-level preferences persisted server-side and cached locally.

| Setting | Options |
|---------|---------|
| **Language** | Spanish (`es`) · English (`en`) |
| **Theme** | Light · Dark |
| **Compact mode** | Reduces spacing for higher information density |
| **Reduced motion** | Minimizes CSS transitions (accessibility) |

- On startup, preferences are loaded from the API (`GET /api/me/preferences`) and applied immediately; `localStorage` acts as a fast fallback while the request is in flight.
- Changes are applied instantly and saved to `localStorage`; API saves are debounced (500 ms) via `PUT /api/me/preferences` so rapid toggles don't flood the server.
- Preferences are stored per-user in the Cosmos DB `reference_data` container (`type = "user_preferences"`, `id = user OID`).
- Implemented with Angular reactive signals — changes propagate instantly.

**API Endpoints:**
- `GET /api/me/preferences` — returns the current user's saved preferences (defaults if none stored).
- `PUT /api/me/preferences` — updates and persists the current user's preferences.

**Source:** [frontend/src/app/core/services/](../frontend/src/app/core/services/) · [api/app/routers/user.py](../api/app/routers/user.py)

---

## Health Check

Public liveness probe — no authentication required.

- Endpoint: `GET /api/health`
- Returns `200 OK` when the API is running.

**Source:** [api/app/main.py](../api/app/main.py)

---

## Platform

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Angular · TypeScript · Angular Material · SCSS |
| **Backend** | Python · FastAPI · Pydantic |
| **Database** | Azure Cosmos DB (NoSQL) |
| **Auth** | Azure AD (Entra ID) · MSAL |

### Azure Infrastructure

| Resource | Purpose |
|----------|---------|
| **Cosmos DB** | Document store — transactions, accounts, categories, tags, audit |
| **App Service** | Hosts the FastAPI backend |
| **Static Web App** | Hosts the Angular frontend |
| **Key Vault** | Secrets management (connection strings, API keys) |
| **Application Insights** | Monitoring, logging, performance telemetry |

Infrastructure is defined as code using **Bicep** with parameterized environments (`dev`, `prod`).

**Source:** [infra/](../infra/) · [infra/modules/](../infra/modules/) · [infra/parameters/](../infra/parameters/)
