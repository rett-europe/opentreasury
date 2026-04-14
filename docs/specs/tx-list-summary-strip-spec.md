# Transaction List — Sticky Summary Strip & Sticky Header

**Author:** Niobe (Spec / UX Analyst)
**Requested by:** Pedro (perocha)
**Date:** 2026-04-13
**Status:** Recommendation — pending Pedro's approval

---

## Problem Statement

The transaction list page has a summary footer **at the bottom** of a scrollable table showing totals (income, expenses, net, transaction count, uncategorized count, transfers). Pedro needs these totals **always visible** — especially after filtering by month — without scrolling to see them. Additionally, the table header row should remain visible while scrolling.

### Current Layout

```
┌──────────────────────────────────────┐
│ .sticky-header (fixed)               │
│   Page Header ("Transactions" + New) │
│   Filter Bar (2 rows of dropdowns)   │
├──────────────────────────────────────┤
│ .scroll-area (overflow-y: auto)      │
│   mat-table                          │
│     <thead> ← scrolls away           │
│     row 1                            │
│     row 2                            │
│     ...                              │
│     row N                            │
│   Summary Footer ← at bottom         │
└──────────────────────────────────────┘
```

### Data Accuracy Problem

The summary is computed **client-side** from `this.transactions()`, which only contains rows loaded so far (infinite scroll, 100-item pages). If March 2025 has 300 transactions, the totals are **wrong** until all 3 pages load. The API `TransactionListResponse` returns only `items` + `continuationToken` — no aggregate totals. The existing `/api/reports/summary` only supports `year` (no month or other filter params).

---

## UX Recommendations

### 1. Summary Strip Placement — Between filter bar and table

**Recommendation:** Move the summary from the bottom into a **thin horizontal strip** between the filter bar and the table. Make it part of `.sticky-header` so it never scrolls away.

```
┌──────────────────────────────────────┐
│ .sticky-header (fixed)               │
│   Page Header                        │
│   Filter Bar                         │
│   ▸ Summary Strip (NEW)              │
├──────────────────────────────────────┤
│ .scroll-area                         │
│   mat-table                          │
│     <thead> ← STICKY within scroll   │
│     rows...                          │
└──────────────────────────────────────┘
```

**Design specifics:**

- **Height:** Single row, ~40px. Compact — NOT a card. Think "status bar", not "dashboard widget."
- **Background:** Subtle surface color (`var(--clr-surface-panel)`) with a bottom border, visually distinct from both the filter bar above and the table below.
- **Layout:** Horizontal flex, items spaced with `gap: 24px`, right-aligned (matches current footer).
- **Content (same as current):**
  - Transaction count (muted text)
  - Uncategorized count (warning color, only if > 0)
  - Total Income (green)
  - Total Expenses (red)
  - Net (green if positive, red if negative)
  - Transfers total (only if ≠ 0)

**Why between filter bar and table (not elsewhere):**

| Option | Verdict | Reasoning |
|--------|---------|-----------|
| Inside filter bar | ❌ Rejected | Filter bar is already 2 rows / ~120px tall. Adding totals makes it too heavy. |
| Separate sticky card above table | ❌ Overcomplicated | A card with padding/shadow adds 60-80px. Too much for 6 numbers. |
| Thin strip below filter bar | ✅ Chosen | Minimal height (~40px), clear visual hierarchy, always visible. |
| Floating overlay | ❌ Rejected | Covers content, feels unnatural for a data table page. |
| Keep at bottom + duplicate at top | ❌ Rejected | Redundant. Bottom position has no value if top strip exists. |

### 2. Sticky Table Header — Yes, with a caveat

**Recommendation:** Make the `<thead>` sticky **within the scroll area** using Angular Material's native `sticky: true` on `mat-header-row`. This is the standard pattern for `mat-table` inside a scrollable container.

**Implementation:** On the existing `mat-header-row`:
```html
<tr mat-header-row *matHeaderRowDef="displayedColumns; sticky: true"></tr>
```

The header sticks to the top of `.scroll-area`, not the viewport. This means it sits just below the summary strip — exactly where the eye expects it.

### 3. Screen Real Estate Analysis — Three Sticky Zones

With all three zones sticky, here's the vertical budget on a **1080p screen** (most common for admin work):

| Element | Height | Notes |
|---------|--------|-------|
| Browser chrome + Angular toolbar | ~64px + ~48px | Fixed |
| Page header (title + button) | ~56px | Part of sticky-header |
| Filter bar (2 rows) | ~120px | Part of sticky-header |
| **Summary strip** (NEW) | **~40px** | Part of sticky-header |
| Table header (sticky within scroll) | ~48px | Sticky within scroll-area |
| **Available scroll area** | **~704px** | ~65% of viewport |
| **Total fixed overhead** | **~376px** | |

**Verdict:** 704px of scrollable area comfortably fits 12-14 table rows. For a page used daily with 10-15 new entries, this is fine. The summary strip adds only 40px — a good trade for always-visible totals.

**Responsive note (< 768px):** On smaller screens, consider dropping the summary strip from sticky and letting it scroll with the table. This is a Phase 2 concern — the admin primarily uses a desktop monitor.

---

## 4. Data Accuracy — Server-Side Totals Required

**This is the critical decision.** Showing wrong totals for financial data is worse than showing no totals.

### Recommendation: New API endpoint for filtered summary totals

**Add `GET /api/transactions/summary`** that accepts the same filter params as `GET /api/transactions` but returns only aggregate totals — no rows. This is a single Cosmos DB cross-partition query with `SUM()` / `COUNT()`. Cheap, fast, accurate.

**Endpoint signature:**
```
GET /api/transactions/summary
  ?year=2026
  &month=3                    (optional — omit for full year)
  &accountId=...              (optional)
  &categoryId=...             (optional)
  &subcategoryId=...          (optional)
  &tagId=...                  (optional)
  &transactionType=...        (optional)
  &categorizationStatus=...   (optional)
  &reviewStatus=...           (optional)
```

**Response:**
```json
{
  "transactionCount": 247,
  "uncategorizedCount": 12,
  "totalIncome": 15230.50,
  "totalExpenses": 8920.75,
  "net": 6309.75,
  "transfersTotal": -500.00
}
```

**Why not client-side totals with a "loading" indicator:**

| Approach | Pros | Cons |
|----------|------|------|
| Client-side + loading state | No API change | Wrong totals during scroll. "Partial" badge is confusing. For 300 txns, user must scroll 3 pages before totals are right. Defeats the purpose of "always-visible accurate totals." |
| **Server-side endpoint** | **Accurate from first render. Fast (one query).** | Requires backend work (~1-2 hours). New endpoint to maintain. |

**The admin makes financial decisions from these numbers.** Partial totals labeled "loading..." erode trust. A server-side query for 6 aggregates over a single month partition is < 5 RU in Cosmos DB — negligible cost.

### Frontend behavior with server-side totals:

1. When filters change → fire **two parallel requests**: `GET /api/transactions` (paginated list) + `GET /api/transactions/summary` (totals).
2. Summary strip shows skeleton shimmer (~200ms) while the summary request resolves.
3. Summary strip updates instantly — no dependency on infinite scroll progress.
4. **Remove** the client-side `footerSummary` computed signal. It's now redundant.
5. The old `TransactionSummaryFooterComponent` gets **repurposed** as `TransactionSummaryStripComponent` with identical data shape, different styling (horizontal strip instead of footer bar).

---

## 5. Implementation Plan for Neo & Trinity

### Backend (Morpheus)

1. **New service method** in `TransactionService`:
   - `async def get_filtered_summary(year, month?, accountId?, ...)` → returns aggregated dict
   - Uses a Cosmos DB query: `SELECT COUNT(1) as count, ... FROM c WHERE c.year=@year AND c.month=@month AND c.isDeleted != true ...` with same filter logic as `list_transactions`
   - Python-side aggregation is also fine (reuse `query_for_report` with added filter params) given the data volume (< 1000 txns/month)

2. **New router endpoint** in `routers/transactions.py`:
   - `GET /api/transactions/summary` with same Query params as `list_transactions` (minus pageSize/continuationToken)
   - Returns `TransactionSummaryResponse` schema

3. **New schema** `TransactionSummaryResponse` in `schemas.py`.

### Frontend (Trinity + Neo)

1. **Rename** `TransactionSummaryFooterComponent` → `TransactionSummaryStripComponent`
   - Change CSS from footer style to thin horizontal strip
   - Add skeleton/shimmer loading state (a `loading` input signal)
   - Keep the same `TransactionSummaryData` interface

2. **Move** the summary component in `transaction-list.component.ts` template:
   - From inside `.scroll-area` (after table) → inside `.sticky-header` (after filter bar)
   - Remove `footerSummary` computed signal

3. **Add** `TransactionSummaryService` (or extend `TransactionService`):
   - Method: `getSummary(filters: TransactionFilters): Observable<TransactionSummaryData>`
   - Called in parallel with `list()` on every filter change

4. **Sticky table header:**
   - Add `sticky: true` to `matHeaderRowDef`
   - One-line change

5. **New labels** (2):
   - `loadingSummary` / `cargandoResumen` — for skeleton state aria-label
   - (The existing labels for the summary values are already defined)

### Estimated scope:
- Backend: ~2 hours (endpoint + service method + schema + tests)
- Frontend: ~3 hours (move component, restyle, wire service, sticky header)
- Total: **~5 hours** of implementation work

---

## 6. Open Questions for Pedro

1. **Filter bar collapse?** On busy months, the 2-row filter bar + summary strip + table header = ~264px of fixed content. Would you want a "collapse filters" toggle (chevron icon) that collapses the filter bar to just year/month, expanding on click? Not urgent, but good to consider.

2. **Full-year summary?** When no month is selected (viewing all of 2026), should the summary strip show the full-year totals? This is a cross-partition query in Cosmos — slightly more expensive but still < 50 RU. I'd recommend yes — the admin needs yearly totals too.

3. **Remove the bottom footer entirely?** Or keep it as a redundant "end of list" confirmation? My recommendation: **remove it** — one source of truth for totals.

---

## Decision Summary

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Summary strip goes between filter bar and table, inside `.sticky-header` | Minimum screen real estate cost (~40px), always visible, clear hierarchy |
| D2 | Table header made sticky via `matHeaderRowDef; sticky: true` within scroll area | Standard Angular Material pattern, no custom CSS needed |
| D3 | New `GET /api/transactions/summary` endpoint for accurate totals | Client-side totals from paginated data are unreliable for financial reporting |
| D4 | Summary strip fires independently from list request on filter change | Totals appear before all rows load — faster perceived performance |
| D5 | Remove bottom footer — summary strip is the single source of truth | No redundant UI elements |
