# Neo — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Deploy template spec — codebase audit findings
- **Secrets count:** Reference draft listed 12 secrets. Audit of actual codebase shows only 7 needed — Key Vault references handle COSMOS_ENDPOINT, AZURE_TENANT_ID, AZURE_CLIENT_ID at runtime; COSMOS_KEY is unused in prod (Managed Identity); AZURE_SUBSCRIPTION_ID and AZURE_TENANT_ID are derivable from AZURE_CREDENTIALS JSON.
- **No separate infra workflow needed:** `setup-azure.sh` is comprehensive and idempotent — creates RG, Entra apps (API + SPA with roles/scopes), SP, deploys Bicep, retrieves SWA token, prints all secrets. A deploy-infra.yml would duplicate this for minimal value.
- **Deploy template is only 2 files:** `deploy.yml` workflow + `README.md`. The product repo already has everything else (Bicep, setup script, Dockerfile, frontend token placeholders).
- **Frontend token replacement:** `environment.prod.ts` uses `#{TOKEN}#` delimiters (5 unique tokens). These survive Angular AOT compilation as string literals in output JS. `sed` replacement on compiled JS files works.
- **WEBSITE_RUN_FROM_PACKAGE=1:** Set in `app-service.bicep`. Means read-only filesystem. Backend deploy must pre-install packages into `.python_packages/` and zip. `startup.sh` handles PYTHONPATH.
- **AZURE_CLIENT_ID collision:** This env var is used for JWT validation but `DefaultAzureCredential` also reads it. Flagged for Switch to evaluate renaming.
- **bicepparam `using` path problem:** Putting prod.bicepparam in the deploy repo creates fragile cross-repo relative paths. Decided against it — setup-azure.sh passes params inline.
- **Key file paths:** `api/config.py` (Settings with 5 env vars), `api/startup.sh` (gunicorn + PYTHONPATH), `frontend/src/environments/environment.prod.ts` (5 tokens), `infra/modules/app-service.bicep` (appSettings with Key Vault refs).

### 2026-04-14: Deploy template spec v2 — process failures and corrections
- **Process failure — committed spec to main:** Violated trunk-based development policy by committing directly to main. Pedro caught it. Coordinator had to create `feature/deploy-template` branch and reset main. Lesson: I enforce spec-first discipline on others but didn't follow branching discipline myself. No exceptions, not even for "quick specs."
- **Process failure — skipped Niobe:** The deploy template is a specification. Niobe (spec/UX expert) should have been involved from the start for requirements analysis, adopter journey mapping, and gap identification. I conflated architecture knowledge with spec completeness. Going forward: ALL specs get a Niobe review pass, including Lead-authored ones.
- **Security authority:** Switch has final, non-negotiable say on all security decisions. This is team policy. When Switch says "must fix," it's adopted without debate.
- **Switch's security review transformed the spec:** OIDC federation replaces AZURE_CREDENTIALS (no persistent creds). Secrets reduced from 7 to 1 (SWA token). 8 GitHub Variables for non-sensitive config. Bicep hardening: `disableLocalAuth: true` on Cosmos, `enablePurgeProtection: true` on Key Vault. All Actions SHA-pinned with explicit permissions.
- **AZURE_CLIENT_ID → ENTRA_API_CLIENT_ID:** Resolves the collision with DefaultAzureCredential. Coordinated change across config.py, key-vault.bicep, app-service.bicep, setup-azure.sh.
- **Tank's contributions adopted:** Separate deploy-infra.yml (different permission scopes per workflow — principle of least privilege). sed-before-build (replace tokens in TypeScript source, not compiled JS). Health check with retry for RBAC propagation delay (3 × 60s).
- **Template is now 3 files:** deploy.yml + deploy-infra.yml + README.md. The infra separation serves security (narrower permissions for code deploy) and usability (infra changes are rare, code deploys are frequent).
- **Versioning strategy added:** GitHub Releases with semver tags. product_ref input already supports tags. Adopters watch releases, set tag, redeploy. No new infrastructure needed.
- **Adopter lifecycle designed:** Full journey from discovery → provisioning (~30 min) → day-2 ops → upgrading → troubleshooting. Persona: NGO admin/IT coordinator, not a developer.

### 2026-04-14: Split transactions technical research (Phase 3)
- **Data model decision: Embedded split lines (Option C — with `splitCategoryIds` convenience array).** Embedded is the clear winner over separate documents: atomic writes, single reads, zero migration, matches existing codebase patterns (subcategories, notes are both embedded). Separate documents introduce multi-document consistency issues, query contamination, and N+1 reads — all for no benefit at NGO scale.
- **API design decision: Batch operations (POST/PUT/DELETE /split).** Atomic batch maps 1:1 to the embedded model. No intermediate invalid states, trivial validation. Individual line CRUD solves a problem we don't have (large collections of sub-resources, not 2-5 categorization entries).
- **Cosmos DB analysis:** 2MB document limit is a non-concern (20 split lines × 250 bytes = 5KB). RU cost for embedded is optimal (single point-read). Separate docs would cost 3-5x more per page load.
- **Report impact:** Only `get_by_category()` needs modification — Python-side unrolling of `splitLines`. Summary/trend/account reports use parent amount and are unaffected. `aggregate_filtered` needs a minor change for uncategorized count.
- **Export impact:** Unroll split lines into separate Excel rows. Import needs no changes (splitting is post-import).
- **Key design constraint:** `splitLines[].amount` sum MUST equal parent `amount`. Validated on every write. No draft/partial splits.
- **Open questions for Pedro:** Split line cap (recommended 20), unsplit behavior (recommended → uncategorized), transfers/refunds splittable.
- **Open questions for Niobe:** Split dialog UX, list view indicator, re-categorization frequency (determines if PATCH endpoint needed).

### 2026-04-16: Date range filter — architecture analysis
- **Current paging architecture:** Frontend walks months 12→1 (or single month), PAGE_SIZE=100, using Cosmos continuation tokens per-partition. Aggregates computed server-side per-partition on first page.
- **Partition key architecture:** `YYYY-MM` partition key is deeply embedded — `list_by_partition()` takes a single partition_key, `aggregate_filtered()` is partition-scoped. Cross-partition queries exist only in `query_for_export()` (no partition_key param, full container scan, higher RU).
- **Recommended: Alternative D** — replace year/month dropdowns with `MatDateRangeInput`, frontend computes overlapping `YYYY-MM` partitions from the date range, fetches using existing API (zero backend changes). The `currentMonth`/`minMonth` waterfall adapts naturally.
- **Key insight:** For 200–500 tx/year, client-side aggregation is trivial — no need for server-side cross-partition aggregate queries. Export already proves cross-partition date queries work, but that pattern (full container scan) shouldn't be used for interactive browsing.
- **Material components:** `MatDateRangeInput` + `MatDatepicker` is the standard Angular Material approach. No custom slider needed. Preset buttons ("This month", "Last 30 days", "This quarter") complement the range picker.
- **`TransactionFilters` interface change:** `year: number` + `month: number | null` → `dateFrom: string` + `dateTo: string`. Cascading change through `loadTransactions()` and `TransactionQueryParams`.
- **Cross-year ranges:** Alternative D naturally supports "Dec 2025 – Jan 2026" by computing partitions `2025-12` + `2026-01`. Current year-dropdown can't do this.

### 2026-04-18: Phase B kickoff — B.0 decisions PR
- **Gate discipline held:** Phase A (PR #15) merged ~20 minutes before this session. Resisted the temptation to "just start writing SQLite repos" — Phase B has three architectural decisions that must land first or the parity tests have nothing to assert against. PR B.0 is pure markdown.
- **B-1 mapping decision — option (a):** SQLite repos own the snake_case ↔ camelCase translation via private `_to_doc`/`_from_doc` helpers. Option (b) would have touched every service. The Cosmos document shape is now the canonical contract by virtue of (1) being what every service speaks, (2) what every API response serializes, (3) what the existing test suite asserts. SQLite adapts; services don't move.
- **B-2 schema-gap inventory — fixed list of 8 items:** 6 column adds to `transactions` (`is_split`, `split_lines`, `bank_description`, `detail`, `reviewed_by_email`, `tag_ids` renaming `tags`), 1 audit_log addition (`metadata`), 1 categories shape assertion. Defining this as a *decision* (not a Morpheus-discovered list inside PR B.2) is the only way to bound B.2 scope and let B.3's parity tests assert against a fixed contract.
- **B-4 Electron shell — locked 7 architectural calls:** electron-builder; ng serve in dev / file:// in prod; child_process sidecar with SIGTERM-then-SIGKILL; **HTTP-only loopback (Switch gate, non-negotiable, no IPC for data, no nodeIntegration)**; ephemeral port + preload-injected `window.__OT_API_BASE__`; top-level `desktop/` workspace (sibling of `frontend/` and `api/`); B.8 ships dev workflow only, no installer (Phase E) and no identity (Phase C).
- **PR slicing held:** B.0 ships only the decisions. B.1 (spec amendment, Niobe), B.2 (migration, Morpheus), B.3 (parity harness, Cypher), B.4–B.7 (SQLite repos, Morpheus), B.8 (Electron shell, Trinity+Tank), B.9 (runbook, Oracle) each get their own PR with one owner. The temptation to bundle B.0+B.1 was rejected — different owners, different review lenses (architectural vs UX/spec).
- **Process note:** This PR lives on the inherited `copilot/proceed-with-phase-b` branch rather than a fresh `feature/electron-phase-b` integration branch as the plan recommended, because the agent session is bound to this branch. Integration-branch creation is for the Coordinator on the next slice; B.0 is small and self-contained enough that branch identity doesn't change the review.
