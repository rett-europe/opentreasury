# System Settings — Main-Alignment Delta

**Author:** Neo (Lead / Architect)
**Date:** 2026-04-18
**Branch:** `feature/system-settings-issue-12`
**Status:** Architecturally signed off — implementation cleared with binding amendments A3, A4, A5.

> Companion document to `docs/specs/system-settings-spec.md`. The spec stays the source of truth for *what* the feature is. This delta records *how the spec lands on the code as it exists today* after main absorbed several features between spec approval and implementation kickoff.

---

## 1. Summary

The approved System Settings spec remains architecturally sound. Between approval (2026-04-18 morning) and implementation kickoff, main absorbed four features that introduce new format-sensitive surfaces the spec did not enumerate: **Balance section** (PR #13), **Date range filter with presets** (PR #9), **Split transactions UI** (`feature/split-transactions`), and an **auth refactor** (`cab41d5`). The API contract, storage model, and admin model are unchanged. Three precision amendments (A3–A5) and a 13-task implementation breakdown follow.

---

## 2. Impact Inventory

| Merged change | Spec section it touches | Required action |
|---------------|-------------------------|-----------------|
| Balance section (`balance.component.ts`, ~793 LOC) | §3 (currency surfaces), §4 (renderers) | Implementation note — 5 currency pipes to retrofit |
| `report_service.py` balance flow | None directly | None |
| Date range filter (`tx-filter-bar`, presets) | §3 (date format) | Implementation note — `MatDateRangeInput` is browser-locale-driven; preview labels use configured format |
| Split transactions dialog | §3 (currency) | Implementation note — 3 currency pipes |
| Transaction list + summary footer | §3 (currency, date) | Implementation note — 6 pipes |
| Dashboard KPI strip + recent-tx table + account grid | §3 (currency) | Implementation note — 5 pipes; **A2 critical path** |
| Reports page | §3 (currency) | Implementation note — 8 pipes |
| Export filename (existing + new) | §6 storage of date format | **Spec amendment A4** — filename always uses ISO `YYYY-MM-DD` regardless of display setting |
| Date format token mapping (`DD/MM/YYYY` → `dd/MM/yyyy`) | §3 / §10 | **Spec amendment A3** — explicit token mapping table |
| Currency pipe call shape consistency | §10 | **Spec amendment A5** — standardise on `currency : code : 'symbol' : '1.2-2'` |
| Auth refactor (`cab41d5`) | §10 admin model | **None** — `get_current_admin` and frontend `adminGuard` unchanged. Switch confirms (see security review). |

---

## 3. New Format-Sensitive Surfaces (post-spec)

| Symbol / file | Type | Notes |
|---------------|------|-------|
| `balance.component.ts` lines 78, 82, 86, 160, 234 | currency | KPI cards + table rows |
| `transaction-list.component.ts` lines 173, 224 | currency | TX amounts + split detail amounts |
| `transaction-list.component.ts` line 102 | date | TX row date column |
| `tx-summary-footer.component.ts` lines 40, 43, 48, 52 | currency | 4 totals |
| `split-dialog.component.ts` lines 55, 58, 65, 68 | date + currency | Split editor |
| `quick-categorize-dialog.component.ts` lines 40, 42 | date + currency | Quick categorize |
| `kpi-strip.component.ts` lines 17, 22, 27 | currency | Dashboard KPIs (A2 critical) |
| `account-grid.component.ts` line 31 | currency | Dashboard accounts |
| `recent-transactions-table.component.ts` lines 33, 73 | date + currency | Dashboard recent TX |
| `reports.component.ts` (8 occurrences) | currency | Reports tables |
| `export.component.ts` filename builder | date (special — A4) | Always ISO |
| `tx-filter-bar.component.ts` MatDateRangeInput | date (special) | Picker stays browser-locale; preview label uses configured format |

Total: ~40 currency hardcodes, ~5 date hardcodes, plus 2 special cases.

---

## 4. A2 (Bootstrap Order) — Concrete Implications

**Components that must NOT render before `SystemSettingsService.load()` resolves (or falls back to defaults):**

- Dashboard (`kpi-strip`, `account-grid`, `recent-transactions-table`)
- Transactions list page
- Balance page
- Reports page
- Export page (preview, if any)

**Mechanism — choose `APP_INITIALIZER`:**

Why over a route guard: route guards run per-route, easy to forget on a new feature. `APP_INITIALIZER` runs once before the router activates anything. It's centralised in `app.config.ts`, pairs naturally with the existing `ReferenceDataService.load()` (which Trinity should migrate to the same pattern at the same time), and gracefully falls back to defaults on API failure inside `SystemSettingsService.load()`. Add a 1.5 s timeout inside `load()` so a slow Cosmos call cannot stall app boot.

---

## 5. Admin Guard Status (post `cab41d5`)

Switch's review (`docs/specs/system-settings-security-review.md`) confirms:

- Backend `get_current_admin` is unchanged and still uses `"Admin" in payload["roles"]`.
- Frontend `adminGuard` exists and works.
- The PUT handler must use `Depends(get_current_admin)`. The GET handler uses `Depends(get_current_user)` because viewers need to read currency/date format to render the app.
- **No spec change required.** The auth refactor is security-positive (removed dev mock).

---

## 6. Spec Amendments Required

### A3 — Date format token mapping (binding)

**What:** Add an explicit lookup table from persisted tokens to consumer formats.

| Stored token | Angular `DatePipe` pattern | Display example |
|--------------|---------------------------|-----------------|
| `DD/MM/YYYY` | `dd/MM/yyyy` | 18/04/2026 |
| `MM/DD/YYYY` | `MM/dd/yyyy` | 04/18/2026 |
| `YYYY-MM-DD` | `yyyy-MM-dd` | 2026-04-18 |
| `DD MMM YYYY` | `dd MMM yyyy` | 18 Apr 2026 |

**Why:** Without an explicit mapping, every consuming component will roll its own lookup and drift over time.
**Where:** New subsection inserted into spec §10 (rendering rules).
**Binding on:** Trinity (centralise in `core/pipes/date-format.pipe.ts`); Cypher (test the mapping).

### A4 — Export filenames always ISO `YYYY-MM-DD` (binding)

**What:** Export filenames must always use `YYYY-MM-DD` for any date components, regardless of the configured `dateFormat` setting.
**Why:** Display formats can include `/` or spaces, which break filenames on Windows/macOS and complicate parsing scripts NGOs may use. The user's display preference must not bleed into filenames.
**Where:** Spec §6.2 storage — clarify that `dateFormat` governs *display only*. Spec §10 rendering — add filename rule.
**Binding on:** Trinity (frontend filename builder); Morpheus (any backend-built filenames).

### A5 — Currency pipe call shape standard (binding)

**What:** All Angular currency pipe usages must use the four-argument form: `currency : codeSignal() : 'symbol' : '1.2-2'`.
**Why:** Mixing pipe shapes (`'EUR'` vs `'EUR':'symbol'` vs `'EUR':'symbol':'1.2-2'`) yields visually inconsistent renders (symbol vs code, decimal precision). Standardising prevents regressions during the retrofit.
**Where:** Spec §10 rendering rules.
**Binding on:** Trinity (apply during retrofit); Cypher (lint/test for the shape).

---

## 7. Implementation Decomposition (Phase 1 — V1 ship)

| # | Owner | Title | Inputs | Outputs | Depends on | Acceptance |
|---|-------|-------|--------|---------|------------|------------|
| 1 | Morpheus | Pydantic models + repository | spec §6, `categories.py` reference | `api/app/models/system_settings.py`, `api/app/repositories/cosmos/system_settings_repo.py` | none | Repo round-trip test passes; model has `extra="forbid"` |
| 2 | Morpheus | Service + GET/PUT routes (admin-only PUT, A1 enforced) | spec §7, §11; security review §6 | `api/app/services/system_settings_service.py`, `api/app/routers/settings.py` | 1 | All 10 Switch MUSTs covered by tests |
| 3 | Morpheus | Default-seed lazy-create | spec §6 defaults | logic in `system_settings_service` | 1 | First GET on empty DB returns defaults and persists them |
| 4 | Trinity | `SystemSettingsService` + computed signals + `APP_INITIALIZER` | scoping §5 | `core/services/system-settings.service.ts`, `core/models/system-settings.model.ts`, `app.config.ts` | 2 | Boot succeeds with backend up; falls back to defaults with backend down |
| 5 | Trinity | Settings page (admin-only route) | spec §10 | `features/settings/settings.component.ts`, `app.routes.ts`, sidenav entry, i18n keys | 4 | Admin sees the page; viewer redirected; save shows snackbar |
| 6 | Trinity | Currency retrofit — dashboard (KPI, account-grid, recent-tx) | A5 | edits to 3 dashboard components | 4 | All 3 use `currencyCode()`; no hard-coded `'EUR'` left |
| 7 | Trinity | Currency retrofit — transactions (list, footer, split, quick-categorize) | A5 | edits to 4 components | 4 | No hard-coded `'EUR'` left in `features/transactions/` |
| 8 | Trinity | Currency retrofit — balance + reports | A5 | edits to 2 components | 4 | No hard-coded `'EUR'` left in `features/balance/` and `features/reports/` |
| 9 | Trinity | Date retrofit + central `DateFormatPipe` | A3 | new pipe + edits to 4 components | 4 | All date pipes consume `systemSettings.dateFormatToken()` via the pipe |
| 10 | Trinity | Export filename hardening (A4) | A4 | edits to `export.component.ts` / export service | 4 | Filenames always `YYYY-MM-DD` regardless of setting |
| 11 | Trinity | Mock API GET/PUT `/api/settings` | scoping §7 | edits to `mock-data.ts`, `mock-api.interceptor.ts` | 4 | Mock dev mode boots without 404 |
| 12 | Cypher | Backend tests | security review §6, A1 | new file under `api/tests/` | 2 | Pytest passes; all 10 MUSTs covered |
| 13 | Cypher | Frontend tests (service + Settings component + admin redirect + format helpers) | A3, A5 | new specs under `frontend/src/app/` | 5, 9 | Jest passes; coverage on critical paths |
| 14 | Neo | Final architecture review on PR | all | review comments | 12, 13 | PR meets sign-off conditions in security review §8 |

Order: 1 → 2 → 3 in series (small backend); 4 in series after 2; 5–11 fan out in parallel from 4; 12 starts after 2 lands; 13 after 5 + 9 land; 14 last.

---

## 8. Risks & Open Questions for Pedro

1. **`MatDateRangeInput` cannot be format-overridden.** The picker input itself stays browser-locale (Material's design). I'm proposing a "selected range" preview label below the picker that uses the configured format. **Confirm OK.**
2. **Migrating `ReferenceDataService` to `APP_INITIALIZER` at the same time.** Pure cleanup, but it's the right moment. **Confirm OK to bundle.**
3. **Container choice for the settings document.** Reusing `reference_data` (Morpheus's leaning) saves an RU floor but mixes concerns; new `system_config` container is cleaner but adds infra. Morpheus to decide in the backend scoping. **No decision needed from you unless you want one.**
