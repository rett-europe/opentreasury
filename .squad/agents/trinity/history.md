# Trinity — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->
- 2026-04-14: Removed "Rett Spain" org-specific branding. Product repo now shows generic "OpenTreasury" brand. Title, toolbar, and theme comments updated. `brand-subtitle` span removed from toolbar — subtitle will be configurable per-org in deployment repos.
- 2026-04-15: **Phase 3 — Split transactions frontend implemented.** Files changed:
  - `transaction.model.ts`: Added `SplitLine`, `SplitLineCreate`, `SplitRequest` interfaces + `isSplit`, `splitCount`, `splitLines`, `splitCategoryIds` fields on `Transaction`.
  - `transaction.service.ts`: Added `createSplit()`, `updateSplit()`, `unsplit()` methods.
  - `labels.type.ts`, `en.ts`, `es.ts`: Added 18 split-related label keys (both languages).
  - `split-dialog.component.ts` (new): Full-width Material dialog with FormArray-based line editor, live balance bar (allocated/unallocated/over-allocated), category/subcategory/tags per line, pre-populate from parent category, auto-fill remainder, unsplit with confirmation.
  - `transaction-list.component.ts`: Split indicator icon (`call_split`) in type column, "Split (N)" label in category column, expand/collapse split lines on row click, split action button in actions column (Admin only), expanded detail panel with indented sub-rows showing amount/category/detail.
  - `mock-data.ts`: Added default split fields to mock transaction factory.
  - Key patterns: signals for reactive balance computation, `FormArray` + `FormGroup` per line, design tokens for all colors/spacing, accessibility (role="button", tabindex, keyboard events on interactive spans).
  - Budget warnings pre-existing (initial bundle 1.07MB vs 500KB budget) — not introduced by this change.
- 2026-04-16: **Date range filter implemented.** Replaced year/month dropdowns with date range picker + preset button strip.
  - `tx-filter-bar.component.ts`: Full rewrite — `TransactionFilters` interface changed from `year/month` to `dateFrom/dateTo` (ISO strings). Added `MatButtonToggleGroup` preset strip (7 presets), `MatDateRangeInput` picker, clear button. Pure helper functions (`getThisMonth()`, `getLastMonth()`, etc.) exported for testability. `applyPreset()` public method for cross-component shortcuts.
  - `transaction-list.component.ts`: Page starts empty (no API call on init). Two distinct empty states: "no range selected" (calendar_today icon + shortcut chips) and "no results in range" (search_off icon). Partition walk from date range (`computePartitions()` generates YYYY-MM keys, newest first). Client-side date boundary trim in `applyClientFilters()`. Client-side summary computation via `computed()` signal using `TRANSACTION_TYPES` constants. Integrated `TransactionSummaryFooterComponent`.
  - `labels.type.ts`, `en.ts`, `es.ts`: Added 12 date-range-related label keys (presets, clear, empty states).
  - Key patterns: `MatDateRangeInput` + `MatDateRangePicker` for range selection, preset buttons deselect on manual date edit, `ViewChild` to call `filterBar.applyPreset()` from empty state chips, `MatChipsModule` for inline shortcuts.
