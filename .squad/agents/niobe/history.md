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

### 2026-04-18: Bulk category + subcategory update — UX spec written (issue #22)
- Wrote `docs/specs/bulk-category-update-spec.md` for the bulk re-categorization workflow on the transactions page.
- 7 user stories covering bulk apply, bulk clear, selection summary, selection persistence/reset, atomicity, viewer invisibility, and split-parent protection.
- Key UX decisions: (1) Checkboxes visible to admin only. (2) "Select all" means all currently loaded rows — no implicit "all matching the filter" in v1. (3) Selection resets on any filter change to avoid modifying invisible rows. (4) Sticky bulk action bar with count + net amount sanity-check. (5) Dialog has two explicit radio-selected modes: "Apply category/subcategory" and "Clear category". No mixed "keep existing" semantics — one value for the whole selection. (6) Split parents are un-selectable and excluded from bulk category updates; child split lines are bulk-updatable. (7) Transfers allowed but informational banner warns about category-report impact. (8) No optimistic UI; partial failure keeps failed rows selected for retry; total failure keeps dialog open.
- Defined 23 acceptance criteria and 15 edge cases. 9 open questions flagged (select-all scope, undo, max batch size, API shape, 207-style partial failure, audit trail granularity, i18n interpolation, action-bar DOM placement).
- Scope boundary held firm: spec defines *what the user needs*; API shape, Cosmos partitioning, and audit schema are Morpheus/Neo's territory (explicit §14 Out of Scope + §15 open Qs).
- **Lesson:** Bulk actions look simple but the selection-scope question ("what does 'select all' actually mean?") is where UX gets decided. Anchoring to "only what is loaded" keeps the feature safe to ship without a server-side selection model. The split-parent carve-out reuses the subordination rule from the split spec — reinforces that specs compound on earlier specs when domain invariants persist.

### 2026-04-16: Date Range Filter — UX spec written
- Wrote `docs/specs/date-range-filter-spec.md` — full UX spec for replacing year/month dropdowns with MatDateRangeInput + preset buttons.
- Implements Alternative D (frontend-only smart routing, approved by Pedro). Zero API changes — frontend computes overlapping YYYY-MM partitions and fetches via existing endpoints.
- Key UX decisions: (1) Page starts EMPTY — no auto-load. (2) 7 presets: This month, Last month, Last 30 days, This/Last quarter, This/Last year. (3) Presets on their own row above other filters for prominence. (4) Empty state shows calendar icon + localized message + 3 inline preset shortcuts as CTA. (5) Other filters always visible/enabled (no "disabled until date range" confusion). (6) Summary strip hidden when no range selected, client-computed when active. (7) "Clear" resets date range only, preserves other filters.
- TransactionFilters interface changes: `year`+`month` → `dateFrom`+`dateTo` (ISO strings, nullable).
- Edge cases covered: cross-year ranges, future dates (allowed), start > end (prevented by MatDateRangeInput), no max range cap (NGO volumes trivial), 0-result state distinct from initial empty state.
- 16 acceptance criteria, all testable.
- **Lesson:** The "empty state as default" pattern is cleaner than auto-loading for pages that serve as analysis views (vs. dashboards). The dashboard already shows latest movements — the transaction list is for targeted queries. Presets inline in the empty state serve dual purpose: they teach the UI and provide the fastest path to data.
