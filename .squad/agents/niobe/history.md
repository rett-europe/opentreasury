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
