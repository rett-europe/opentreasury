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

### 2026-04-18: System Settings spec (Issue #12) approved
- Niobe's `docs/specs/system-settings-spec.md` cleared architectural review. Reuses existing `reference_data` Cosmos container (pk `/type`) with a singleton `id="system"` doc — no new container, no Bicep change, no `CosmosService` edits.
- Two binding amendments folded into §13: **A1** server-authoritative `updatedAt`/`updatedBy` on `PUT /api/settings` (keeps door open for ETag later); **A2** `SystemSettingsService.load()` must complete before the first format-sensitive render to avoid flash-of-wrong-currency.
- All six open questions resolved per recommendation. Drawer ("Preferences") and page ("Settings") naming locked in.
- Hard-coded format surface audited and small: `MAT_DATE_LOCALE: 'es-ES'` in `app.config.ts`, `€` in `kpi-card.component.spec.ts` and `amountEur` label. Refactor footprint is hours, not days.
- Kept `SystemSettingsService` separate from `AppSettingsService` — different sources of truth (server config vs user profile), don't merge them.
- Routing on approval: Morpheus (backend), Trinity (frontend), Cypher (tests) in parallel; Switch courtesy review on the admin-only PUT.

### 2026-04-16: Date range filter — architecture analysis
- **Current paging architecture:** Frontend walks months 12→1 (or single month), PAGE_SIZE=100, using Cosmos continuation tokens per-partition. Aggregates computed server-side per-partition on first page.
- **Partition key architecture:** `YYYY-MM` partition key is deeply embedded — `list_by_partition()` takes a single partition_key, `aggregate_filtered()` is partition-scoped. Cross-partition queries exist only in `query_for_export()` (no partition_key param, full container scan, higher RU).
- **Recommended: Alternative D** — replace year/month dropdowns with `MatDateRangeInput`, frontend computes overlapping `YYYY-MM` partitions from the date range, fetches using existing API (zero backend changes). The `currentMonth`/`minMonth` waterfall adapts naturally.
- **Key insight:** For 200–500 tx/year, client-side aggregation is trivial — no need for server-side cross-partition aggregate queries. Export already proves cross-partition date queries work, but that pattern (full container scan) shouldn't be used for interactive browsing.
- **Material components:** `MatDateRangeInput` + `MatDatepicker` is the standard Angular Material approach. No custom slider needed. Preset buttons ("This month", "Last 30 days", "This quarter") complement the range picker.
- **`TransactionFilters` interface change:** `year: number` + `month: number | null` → `dateFrom: string` + `dateTo: string`. Cascading change through `loadTransactions()` and `TransactionQueryParams`.
- **Cross-year ranges:** Alternative D naturally supports "Dec 2025 – Jan 2026" by computing partitions `2025-12` + `2026-01`. Current year-dropdown can't do this.
