# System Settings — Frontend Scoping

**Author:** Trinity (Frontend Developer)
**For:** Issue [#12](https://github.com/rett-europe/rettreasury/issues/12) — System Settings page retrofit
**Date:** 2026-04-18
**Branch:** `feature/system-settings-issue-12`
**Status:** Scoping — implementation pending Neo's approval of the alignment delta

---

## 1. New Files Needed

| File | Purpose |
|------|---------|
| `frontend/src/app/features/settings/settings.component.ts` | Admin-only standalone component: reactive form with 6 settings fields, save/cancel, snackbar feedback, dirty-state detector. ~250 lines. |
| `frontend/src/app/core/services/system-settings.service.ts` | Injectable service: singleton settings signal, computed helpers `currencySymbol()`, `currencyCode()`, `dateFormatToken()`, `numberLocale()`. Load/save methods. ~180 lines. |
| `frontend/src/app/core/models/system-settings.model.ts` | TypeScript interfaces: `SystemSettings`, enums for `CurrencyCode`, `DateFormat`, `NumberFormat`. ~40 lines. |
| `frontend/src/app/core/pipes/currency-display.pipe.ts` (optional) | Pure pipe wrapping `CurrencyPipe`, injects `SystemSettingsService`, dynamic currency. Useful to avoid hunting every hard-coded `'EUR'`. ~50 lines. |
| `frontend/src/app/core/pipes/date-format.pipe.ts` (optional) | Pure pipe wrapping `DatePipe`, maps persisted token (`DD/MM/YYYY`) → DatePipe pattern (`dd/MM/yyyy`). ~70 lines. |
| `frontend/src/app/shared/guards/system-settings-loaded.guard.ts` (optional) | Route guard or signal wrapper: ensures settings load before route activation (A2). ~40 lines. |

---

## 2. Existing Files to Modify

| File | Changes | Why | Risk |
|------|---------|-----|------|
| `frontend/src/app/app.routes.ts` | Add route `{ path: 'settings', loadComponent: () => …, canActivate: [MsalGuard, adminGuard] }` | New page entry point | Low |
| `frontend/src/app/app.component.ts` | Inject `SystemSettingsService`. Add nav item under Configuration section inside `@if (authService.isAdmin())`. Trigger `systemSettings.load()` (or via `APP_INITIALIZER`). | Menu routing + bootstrap | Low |
| `frontend/src/app/features/transactions/transaction-list.component.ts` | Replace hard-coded `'dd/MM/yyyy'` (line ~102) and `currency: 'EUR'` (lines ~173, ~224) with computed signals | Display configured currency/date | Medium |
| `frontend/src/app/features/transactions/tx-summary-footer.component.ts` | 4 occurrences of `currency: 'EUR'` (lines ~40, 43, 48, 52) | Footer totals in configured currency | Low |
| `frontend/src/app/features/transactions/split-dialog.component.ts` | Date (line ~55) + 3 currency occurrences (lines ~58, 65, 68) | Split dialog formatting | Medium |
| `frontend/src/app/features/transactions/quick-categorize-dialog.component.ts` | Date + currency hardcodes (lines ~40, 42) | 2 changes | Low |
| `frontend/src/app/features/balance/balance.component.ts` | 5 occurrences of `currency: 'EUR'` (lines ~78, 82, 86, 160, 234) | New balance KPIs must respect setting | Medium |
| `frontend/src/app/features/dashboard/kpi-strip.component.ts` | 3 KPI cards with `currency: 'EUR'` (lines ~17, 22, 27) | Critical bootstrap path (A2) | Medium |
| `frontend/src/app/features/dashboard/account-grid.component.ts` | 1 currency hardcode (line ~31) | Dashboard accounts | Low |
| `frontend/src/app/features/dashboard/recent-transactions-table.component.ts` | Date (line ~33) + currency (line ~73) | Recent TX list on dashboard | Low |
| `frontend/src/app/features/reports/reports.component.ts` | 8 currency occurrences (lines ~56, 64, 72, 93, 99, 123, 129, 135) | Reports rendering | Medium |
| `frontend/src/app/features/export/export.component.ts` | Inject `SystemSettingsService`; pass `dateFormatToken()` to export service for filename sanitization (always ISO `YYYY-MM-DD` per A4) | Export filename + preview | Medium |
| `frontend/src/app/core/i18n/labels.type.ts` | Add 16 new label keys (per spec §10); update 2 existing for drawer rename ("Settings" → "Preferences") | Type-safe label support | Low |
| `frontend/src/app/core/i18n/en.ts` | Add 16 EN translations; update 2 existing | EN labels | Low |
| `frontend/src/app/core/i18n/es.ts` | Add 16 ES translations; update 2 existing | ES labels | Low |
| `frontend/src/app/app.config.ts` | Register `APP_INITIALIZER` for `SystemSettingsService.load()` | A2 bootstrap | Low |
| `frontend/src/app/core/mocks/mock-api.interceptor.ts` | Add GET + PUT `/api/settings` handlers | Mock dev mode | Low |

---

## 3. Currency-Formatted Surfaces

| File | Approx. lines | Current | Target |
|------|--------------|---------|--------|
| `balance.component.ts` | 78–86, 160, 234 | `currency:'EUR':'symbol':'1.2-2'` × 5 | `currency: systemSettings.currencyCode():'symbol':'1.2-2'` |
| `transaction-list.component.ts` | 173, 224 | Hard-coded `'EUR'` | Dynamic |
| `tx-summary-footer.component.ts` | 40–52 | Hard-coded `'EUR'` × 4 | Dynamic |
| `split-dialog.component.ts` | 58, 65, 68 | Hard-coded `'EUR'` × 3 | Dynamic |
| `quick-categorize-dialog.component.ts` | 40 | Hard-coded `'EUR'` | Dynamic |
| `kpi-strip.component.ts` | 17–27 | Hard-coded `'EUR'` × 3 | Dynamic — **A2 critical** |
| `account-grid.component.ts` | 31 | Hard-coded `'EUR'` | Dynamic |
| `recent-transactions-table.component.ts` | 73 | Hard-coded `'EUR'` | Dynamic |
| `reports.component.ts` | 56, 64, 72, 93, 99, 123, 129, 135 | Hard-coded `'EUR'` × 8 | Dynamic |

**Total:** ~40 hard-coded currency values across 11 components.

---

## 4. Date-Formatted Surfaces

| File | Approx. lines | Current | Target |
|------|--------------|---------|--------|
| `transaction-list.component.ts` | 102 | `\| date: 'dd/MM/yyyy'` | Map `systemSettings.dateFormatToken()` → DatePipe pattern, then apply |
| `split-dialog.component.ts` | 55 | `\| date: 'dd/MM/yyyy'` | Dynamic |
| `quick-categorize-dialog.component.ts` | 42 | `\| date: 'dd/MM/yyyy'` | Dynamic |
| `recent-transactions-table.component.ts` | 33 | `\| date: 'dd/MM/yyyy'` | Dynamic |
| `tx-filter-bar.component.ts` | preset functions | `MatDateRangeInput` driven by browser locale; preset labels are i18n strings (not date-formatted) | **Special case** — see note below |
| `export.component.ts` | filename builder | Uses display format | Per **A4**: filename always uses ISO `YYYY-MM-DD` regardless of setting |

**Filter bar special case:** `MatDateRangeInput` does not accept a format parameter — it is driven by Angular's locale. Recommendation: keep the picker as-is (browser locale on the calendar UX), but render a small "selected range" preview label below the picker using the configured format token. Avoid forcing a format on Material's component. Flagged in §8 for Neo.

---

## 5. Bootstrap Strategy for A2

**Choice: `APP_INITIALIZER`** in `app.config.ts`.

```typescript
export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: APP_INITIALIZER,
      useFactory: (s: SystemSettingsService) => () =>
        s.load().catch(() => {
          console.warn('System settings load failed; using defaults');
          return Promise.resolve();
        }),
      deps: [SystemSettingsService],
      multi: true,
    },
    // …existing providers
  ],
};
```

**Why this and not the alternatives:**
- Centralized in one place — no scattered constructor calls or per-route guards.
- Async errors are caught; defaults already populated in the service signal kick in transparently.
- The router does not activate any route until all `APP_INITIALIZER` factories resolve, so the dashboard, transactions list, and balance page never render before settings are known.
- Pairs naturally with the existing `ReferenceDataService.load()` if Neo wants to migrate that to `APP_INITIALIZER` too.

**Mitigation for slow API:** add a 1.5 s timeout inside `SystemSettingsService.load()` — fall back to defaults rather than blocking the app indefinitely.

---

## 6. Sidenav Integration

Insert under the existing `@if (authService.isAdmin())` Configuration block in `app.component.ts` (after the Accounts entry):

```html
<a class="nav-item" routerLink="/settings" routerLinkActive="active" (click)="closeMobileNav()">
  <mat-icon>settings</mat-icon>
  <span>{{ settings.labels().systemSettings }}</span>
</a>
```

Admin visibility comes from the surrounding `@if`. The route itself uses `canActivate: [MsalGuard, adminGuard]` (defense in depth — frontend guard for UX, backend `get_current_admin` for enforcement).

---

## 7. Mock API Updates

Add to `frontend/src/app/core/mocks/mock-data.ts`:

```typescript
export const MOCK_SYSTEM_SETTINGS = {
  id: 'system',
  type: 'system_settings',
  currency: 'EUR',
  dateFormat: 'DD/MM/YYYY',
  numberFormat: 'eu',
  fiscalYearStartMonth: 1,
  defaultLanguage: 'es',
  organizationName: 'Demo Org',
  updatedAt: '2026-04-18T10:00:00Z',
  updatedBy: 'mock-oid-admin',
};
```

Add to `mock-api.interceptor.ts`:

```typescript
if (path === '/api/settings' && method === 'GET') {
  return of(json(MOCK_SYSTEM_SETTINGS)).pipe(delay(randomDelay()));
}
if (path === '/api/settings' && method === 'PUT') {
  const body = req.body as Record<string, unknown>;
  const updated = {
    ...MOCK_SYSTEM_SETTINGS,
    ...body,
    updatedAt: new Date().toISOString(),
    updatedBy: 'mock-oid-admin',
  };
  return of(json(updated)).pipe(delay(randomDelay()));
}
```

Add basic enum validation that returns 400 for out-of-range values, mirroring the backend.

---

## 8. Risks / Questions for Neo

1. **Centralised format mapping.** Recommend a single `DateFormatPipe` in `core/pipes/` so the `DD/MM/YYYY → dd/MM/yyyy` mapping lives in one place. Otherwise every component duplicates the lookup.
2. **MatDateRangeInput formatting.** Picker input is browser-locale-driven; we cannot force the configured format on it. Confirm Pedro accepts the picker staying browser-locale with a "selected range" preview label that uses the configured format.
3. **Export filename ownership.** Frontend currently builds export filenames. Per A4 they should always be ISO `YYYY-MM-DD`. Confirm filename construction stays frontend-side and Morpheus's backend export endpoint also enforces ISO if it ever generates filenames server-side.
4. **APP_INITIALIZER convergence.** Recommend migrating `ReferenceDataService.load()` to the same `APP_INITIALIZER` pattern at the same time so bootstrap is a single coherent step. Pure cleanup — flag for Neo's call.

---

## 9. Summary

- **6 new files**, **17 modified files**.
- ~40 currency hardcodes + ~5 date hardcodes to retrofit.
- Bootstrap via `APP_INITIALIZER` to satisfy A2.
- Sidenav entry inside the existing admin-only Configuration block.
- Mock API adds GET + PUT `/api/settings` for dev parity.
