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
