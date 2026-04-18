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

### 2026-04-18: Electron + SQLite desktop spec — UX review
- Reviewed Neo's `docs/specs/electron-sqlite-spec.md` §6/§7/§9 from a UX angle. Verdict: **Needs UX additions**. Tech is solid; user-visible surface is largely missing.
- **Mode-entry gap:** §6.1 lists three modes but never describes the cold-launch decision screen. Without a first-run mode picker, the user has no described path into Local vs Team vs Cloud. Phase C must include a mode-selection screen.
- **Mode-switching gap:** Spec is silent on switching modes after first run (e.g., Local user wants to migrate to Team). Recommended a persistent "current mode + identity" status chip in the app chrome that doubles as the entry point for switch / sign-out / disconnect OneDrive.
- **Name prompt timing (§6.2):** "First launch" is ambiguous — first app launch or first DB created? Recommended: prompt appears after first DB created, before first write. Skippable (falls back to OS username). Editable later via Settings → Identity.
- **OneDrive flow error states (§6.3):** Spec covers happy path only. Missing: MSAL popup blocked by browser/policy, user cancels MSAL, user cancels folder picker, account has no OneDrive provisioned, network offline, silent-refresh fails on relaunch (re-prompt vs degrade-to-read-only?). Each needs a defined recovery path.
- **Read-only OneDrive folder (§6.4):** "SQLite blocks writes at OS level. No app code needed" is technically true but UX-toxic — the user gets `SQLITE_READONLY` errors. App must detect read-only at startup and show a friendly read-only banner + disable write actions in the UI. Save/Edit/Delete buttons must be visibly disabled with a tooltip explaining the OneDrive permission.
- **Shared-mode contention UX (§7):** Lock retry / conflict detection mechanics defined but the user-facing experience isn't. Recommended: silent retry with toast on >2s wait, modal with "Sarah is editing — waiting..." after 5s, conflict-resolution dialog with "Keep mine / Keep theirs / View diff" on optimistic-concurrency conflict. Avoid spinner-of-death.
- **Sign-out flow:** Not mentioned anywhere. Team mode needs explicit sign-out (clear MSAL cache, return to mode picker). Should warn if shared DB has uncommitted local changes.
- **Phase C scope:** Labeled "Identity + security" but UX deliverables not enumerated. Risks Trinity inventing UX during implementation. Listed the deliverables explicitly: mode picker, name prompt, status chip, OneDrive connect/disconnect, read-only banner, sign-out confirmation, contention UX.
- **Lesson — desktop modes need a "shell language":** Web apps lean on the URL bar + login state for context. Desktop apps don't. The user must be told at all times: which mode am I in, who am I, where is the data, can I write. A persistent status chip + consistent banner pattern carries that load. This is the same lesson as the empty-state-as-default principle — make the system state visible by default, not on demand.
- **Lesson — explicit mode entry is also a UX win:** Neo's "no silent OneDrive detection" decision (§6.3) is technically correct AND user-experientially correct. A user who clicks "Connect to OneDrive" *understands* they're entering shared mode. A user whose app silently flipped modes because of a path heuristic doesn't. Trust comes from explicitness.
- Key files: `docs/specs/electron-sqlite-spec.md`, `.squad/decisions/inbox/niobe-electron-spec-ux.md`
