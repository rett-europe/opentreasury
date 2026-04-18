# Niobe — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Deploy template spec — adopter experience review
- Reviewed Neo's deploy-template-spec.md from an adopter UX perspective. The spec is technically solid (2-file template, DRY architecture) but written by engineers for engineers.
- Defined the realistic adopter persona: "Ana" — NGO IT contact, Windows user, can follow instructions but doesn't know Bicep/GitHub Actions/service principals.
- Mapped the full adopter lifecycle: Discovery → Evaluation → Prerequisites → Provisioning → First Deploy → First Use → Operations. The spec only covers Provisioning + First Deploy.
- **Critical gap:** Post-deployment onboarding is completely missing — no guidance on Entra role assignment, first account/category setup, or first import.
- **Critical gap:** Script output names don't 1:1 match GitHub secret names — high confusion risk for adopters.
- **Critical gap:** Windows/PowerShell path not mentioned in spec despite `setup-azure.ps1` existing.
- **30-minute claim is unrealistic.** Mapped actual steps: optimistic = 28 min, realistic = 82 min. Recommended changing to "about an hour" with qualifier.
- Versioning UX has significant gaps: no notification mechanism, `product_ref` is git-speak, default to `main` means deploying unreleased code, no rollback documentation.
- Key files: `docs/specs/deploy-template-spec.md`, `scripts/setup-azure.sh`, `scripts/setup-azure.ps1`, `docs/guides/azure-setup.md`
- **Lesson:** Technical specs need persona-first thinking. The adopter lifecycle extends far beyond "deploy completes." Post-deployment onboarding, versioning, and error recovery are where adoption succeeds or fails.
- Asked to be involved in writing the deploy template README.

### 2026-04-14: Deploy template README — adoption guide written
- Created `deploy-template/README.md` — full end-to-end adoption guide for NGO admins.
- Persona-first writing: "Ana" (most technical person at a 20-person NGO) is the target reader. No developer jargon.
- Structure: 18 sections covering the complete adopter lifecycle — discovery through teardown.
- Incorporated all review recommendations: outcomes-first intro, realistic "about an hour" estimate, cost table upfront, Windows/PowerShell parity, post-deployment onboarding (Entra role assignment, first account, first import), error recovery ("safe to re-run"), health-check verification checklist, symptom→check→fix troubleshooting for all known gotchas.
- Key design decisions: both bash and PowerShell commands shown for every CLI step; Azure Portal navigation spelled out step-by-step (e.g., "Enterprise Applications, not App registrations"); cost monitoring and budget alerts section added.
- **Note for Tank/Oracle:** The script output format (Step 9) in both `setup-azure.sh` and `setup-azure.ps1` still prints the legacy `AZURE_CREDENTIALS` secret and doesn't match the OIDC-based 1-secret + 8-variable classification from the spec. The scripts need updating to match the README's guidance. Filed as a decision.
- Key files: `deploy-template/README.md`, `docs/specs/deploy-template-spec.md`

### 2026-04-14: Phase 3 — Split Transactions spec written (FR-022–025)
- Wrote complete SDD spec at `docs/specs/phase-3-split-transactions-spec.md`.
- 7 user stories covering split creation, independent categorization, live balance tracking, validation, editing, unsplitting, and list visibility.
- 4 real-world scenarios from Pedro's descriptions: remesa (12 member payments), multi-cost-center supplier payment, dual-grant incoming payment, mixed-category reimbursement.
- 5 Mermaid flow diagrams: overall user journey, add-lines flow, save/validation flow, unsplit flow.
- Split editor design: full-width MatDialog with parent summary header, live balance bar (allocated/unallocated with progress), scrollable split lines table, tab-optimized keyboard entry.
- Transaction list integration: collapsed view with split badge, expandable child rows.
- Comprehensive edge cases (14): single-line invalid, full-amount line, already-categorized parent, imported vs manual, parent category subordination, parent amount change → rebalance required, currency inheritance, soft-delete cascade, audit trail, transfer pair independence, max 50-line soft limit, duplicate lines allowed, categorizationStatus per-line, reviewStatus on parent only.
- Reporting impact: category reports use split lines, account/summary/strip use parent amount, search matches against split line fields.
- 7 open questions flagged for Pedro/Neo/Morpheus: max line limit, export format, pre-populate first line, split status filter, notes inheritance, duplicate-line shortcut, auto-fill remainder.
- **Key decisions made:** (1) Minimum 2 lines per split. (2) Parent amount is the financial anchor — never modified by splits. (3) Split lines inherit parent's transactionType and currency implicitly. (4) Category reports use split line categories, not parent's. (5) Review status lives on parent only. (6) Parent amount change after split → warning badge, must rebalance.
- **Lesson:** Split transactions are the intersection of bank-level truth (parent) and business-level truth (lines). The spec must clearly separate what the bank says (parent amount, description) from what the org needs (categorization, cost allocation). This duality drives most of the edge cases.

### 2026-04-16: Date Range Filter — UX spec written
- Wrote `docs/specs/date-range-filter-spec.md` — full UX spec for replacing year/month dropdowns with MatDateRangeInput + preset buttons.
- Implements Alternative D (frontend-only smart routing, approved by Pedro). Zero API changes — frontend computes overlapping YYYY-MM partitions and fetches via existing endpoints.
- Key UX decisions: (1) Page starts EMPTY — no auto-load. (2) 7 presets: This month, Last month, Last 30 days, This/Last quarter, This/Last year. (3) Presets on their own row above other filters for prominence. (4) Empty state shows calendar icon + localized message + 3 inline preset shortcuts as CTA. (5) Other filters always visible/enabled (no "disabled until date range" confusion). (6) Summary strip hidden when no range selected, client-computed when active. (7) "Clear" resets date range only, preserves other filters.
- TransactionFilters interface changes: `year`+`month` → `dateFrom`+`dateTo` (ISO strings, nullable).
- Edge cases covered: cross-year ranges, future dates (allowed), start > end (prevented by MatDateRangeInput), no max range cap (NGO volumes trivial), 0-result state distinct from initial empty state.
- 16 acceptance criteria, all testable.
- **Lesson:** The "empty state as default" pattern is cleaner than auto-loading for pages that serve as analysis views (vs. dashboards). The dashboard already shows latest movements — the transaction list is for targeted queries. Presets inline in the empty state serve dual purpose: they teach the UI and provide the fastest path to data.

### 2026-04-18: Multi-sheet Excel import — UX spec written (issue #17)
- Wrote `docs/specs/multi-sheet-import-spec.md` for issue #17 (allow user to pick which sheet to import when an `.xlsx` workbook contains several movements-shaped sheets).
- Today's behavior: `_find_movements_sheet` silently picks the *first* sheet whose first 12 rows contain the four required headers. Other candidate sheets are dropped with no signal — confusing for archive workbooks (one sheet per year).
- Core UX decision: **two-call preview**. First call (no `sheet` param) is *discovery* — returns either the normal preview (0 or 1 candidate, behavior unchanged) or a new `requiresSheetSelection: true` payload listing candidates + reasons for ignored sheets. Second call (`sheet={name}`) does the actual validation. This avoids paying parse cost for sheets the user is not going to import, and lets the single-sheet case stay one-click as it is today.
- Designed the discovery payload to also list **ignored** sheets with a reason (`missing_required_headers` + which headers, or `empty`) — closes the "the file looks fine, why won't it import?" support gap without adding much code.
- Added a small "Sheet: {name}" badge on the preview card for **both** paths (single- and multi-sheet) so the user is never ambiguous about what they're committing.
- State machine rule for the picker: changing the sheet selection after a successful preview clears the preview and disables Confirm until re-previewed. Prevents committing data the user did not actually validate.
- Backwards compatibility: import endpoint's `sheet` param is optional; omitting it keeps today's "first candidate wins" behavior so legacy API callers (if any) are unaffected. Frontend ships in lockstep with API, so the new `requiresSheetSelection` shape is acceptable for the Angular client.
- 10 edge cases nailed down up-front, including: URL-unsafe sheet names (Año 2026 / Caja #1), Categories sheet that coincidentally also has the four movements headers, 50+ candidate sheets (Pedro's archive case), and the "user changes the picker after a valid preview then clicks Confirm" trap.
- 15 acceptance criteria, all directly testable.
- 5 open questions flagged for Pedro / Morpheus / Trinity / Switch — most importantly Q-1 (is `dataRowCount` cheap enough to compute during discovery on a 50-sheet workbook).
- Explicit non-goals listed: importing multiple sheets in one run, per-sheet account mapping, remembering last-picked sheet — all real future ideas, kept out so reviewers don't conflate scope.
- **Lesson:** When a current behavior is "silently pick the first one," the right UX is rarely "always ask." It's "ask only when the choice is actually ambiguous." Splitting the preview into discovery + validation kept the common (single-sheet) path zero-friction while making the multi-sheet path explicit. Same pattern likely applies elsewhere in the app — e.g., account auto-resolution by IBAN.
