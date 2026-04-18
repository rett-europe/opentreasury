# Squad Decisions

## Active Decisions

### 2026-04-18: System Settings spec approved (Issue #12)
**By:** Pedro (approval) + Neo (architectural review)
**What:** `docs/specs/system-settings-spec.md` is **Approved**. V1 ships 6 settings (Currency, Date format, Number format, Fiscal year start, Default language, Organization name) stored as a singleton `id="system"` document in the existing `reference_data` Cosmos container (pk `/type`). New `GET`/`PUT /api/settings` endpoints; PUT is admin-only. New left-menu **Settings** entry behind `adminGuard`. Existing right-side drawer is renamed to **Preferences** (label change only).

Two binding amendments folded into spec §13:
- **A1:** `PUT /api/settings` writes `updatedAt` (server clock, UTC ISO 8601) and `updatedBy` (authenticated principal) server-side — never trust client values. Both fields are returned in `GET` and `PUT` responses. Keeps the door open for ETag/optimistic concurrency later without a data-shape change.
- **A2:** `SystemSettingsService.load()` must complete (or fall back to defaults) before the first format-sensitive render (transactions list, dashboard, KPI strip). Avoids flash-of-wrong-currency / wrong-date-format. Trinity picks the mechanism (router-outlet gate or pipe-level placeholder).

Open questions OQ-1…OQ-6 all resolved per Neo's recommendations: page="Settings"/drawer="Preferences"; 4-currency short list (EUR/USD/GBP/CHF); fiscal year stored now to avoid migration; org name surfaces in browser tab title + export filenames only; `updatedAt`+`updatedBy` is sufficient audit for V1; no extra V1 settings.

**Why:** Reuses existing infrastructure (no Bicep / `CosmosService` / new container), preserves Single Responsibility between per-org `SystemSettingsService` and per-user `AppSettingsService`, ships smallest useful set without forcing a follow-up spec.

**Routing on approval:** Morpheus (backend), Trinity (frontend), Cypher (tests for AC-1…AC-15) in parallel; Switch courtesy review of the admin-only PUT; Neo reviews implementation PRs against the spec before merge.

### 2026-04-10: Project kickoff
**By:** Pedro (user)
**What:** OpenTreasury — open-source bank transaction management for NGOs. Angular frontend, Microsoft Entra ID auth (configurable tenant), Python FastAPI backend with Cosmos DB. Transaction tracking with categories/subcategories.
**Why:** Help NGO administrative staff manage finances properly.

### 2026-04-10: Frontend stack — Angular
**By:** Pedro (user)
**What:** Angular is the frontend framework.
**Why:** User preference / team expertise.

### 2026-04-10: Auth — Microsoft Entra ID
**By:** Pedro (user)
**What:** Microsoft Entra ID with configurable tenant domain. Organization employees only.
**Why:** Organizations use Microsoft 365 / Entra ID for identity management.

### 2026-04-10: Backend stack — Python FastAPI
**By:** Pedro (user directive)
**What:** Backend uses Python FastAPI. Not ASP.NET Core.
**Why:** Easier to maintain for a small NGO team.

### 2026-04-10: Database — Cosmos DB NoSQL (Serverless)
**By:** Pedro (user directive)
**What:** Cosmos DB NoSQL with serverless capacity, not Azure SQL.
**Why:** Flexible schema for model evolution. Serverless scales to zero, cheaper (~€1-5/month).

### 2026-04-12: Mandatory lint enforcement — all agents, all files
**By:** Pedro (user directive)
**What:** Every code-producing agent MUST run full lint locally before reporting work as done. Lint covers ALL files (`app/` + `tests/`), not just changed files. Pre-existing issues from merged branches are your responsibility to fix. CI failures from lint are unacceptable.
**Why:** Repeated CI lint failures wasting Pedro's time.
**Commands:**
- Backend: `flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__`
- Backend format: `black --check app/ tests/ --line-length=120`
- Backend tests: `pytest tests/ -v --override-ini="addopts="`
- Frontend: `npx ng lint`
- Frontend build: `npx ng build --configuration=production`
**Enforced by:** Tank (CI pipeline), Cypher (code review)

### 2026-04-10: User directive — Model override
**By:** Pedro (via Copilot)
**What:** All core agents (Neo, Trinity, Morpheus, Cypher) MUST use `claude-opus-4.6` as their model. Scribe stays on `claude-haiku-4.5` (fast tier).
**Why:** User request — captured for team memory.

### 2026-04-10: Architecture approved
**By:** Pedro (user)
**What:** Approved architecture: Python FastAPI + Cosmos DB NoSQL (Serverless) + Angular + Azure Static Web Apps + App Service B1 + Bicep IaC + GitHub Actions CI/CD. Compute is container-based (Dockerfile) for portability — can swap App Service for Container Apps later without code changes.
**Why:** Cost-effective (~€20-25/month), flexible schema, easy to maintain, compute-agnostic.

### 2026-04-10: Feature decisions from Q&A
**By:** Pedro (user)
**What:** Bank accounts: multiple banks, entity = bank name + IBAN. Categories/subcategories: admin picks from pre-defined list. Tags: flat, pre-defined list. RBAC: Admin + Viewer. Excel import: deferred complex mapping. Export: Excel sufficient. i18n: Spanish primary, English secondary, extensible.
**Why:** Direct user input on feature scoping.

### 2026-04-10: Feature requirements
**By:** Pedro (user)
**What:** Admin fills Excel daily, one sheet per bank account (typically 4-5 sources). All EUR. Daily routine: 10-15 transactions from bank export. Feature requests: multi-account support, i18n, categories+subcategories, tagging, search, Excel import (killer feature), Excel export, future PowerBI analytics.
**Why:** Real workflow requirements from an NGO admin's daily Excel process.

### 2026-04-10: RBAC finalized
**By:** Pedro (user)
**What:** Two roles — Admin (full access including creating categories/tags/accounts) and Viewer (read-only). Worker is Admin. No approval workflows.
**Why:** Worker shouldn't be a bottleneck. Audit trail provides accountability.

### 2026-04-10: Design review approved — full feature build authorized
**By:** Pedro (user)
**What:** Approved comprehensive design: updated data model (5 containers, signed amounts, reference_data container for tags+accounts), 7 screens, sidebar navigation, 26 API endpoints, RBAC (Admin/Viewer), i18n (es/en), speed-optimized transaction form (~15s/entry target).
**Why:** All requirements from Q&A sessions addressed.

### 2026-04-10: Test strategy adopted
**By:** Cypher (Tester)
**What:** Heavy unit tests on money math, practical integration tests on API flows, lightweight E2E on critical paths. Stack: pytest + pytest-asyncio + httpx AsyncClient + pytest-cov + unittest.mock + factory_boy + Decimal assertions.
**Why:** NGO app tracking real money — cannot afford bugs in financial calculations.

### 2026-04-10: Backend implementation decisions
**By:** Morpheus (Backend Dev)
**What:** Auth via python-jose + JWKS (1hr cache). Singleton async CosmosService. Cosmos continuation tokens for pagination. Python-side aggregation for reports. Decimal in Pydantic, float in Cosmos (Decimal(str(float_val)) conversion). CamelModel base for camel/snake bridging. Transaction update requires year+month params. No physical deletes. Global error handler for Cosmos errors. Health endpoint at GET /api/health.
**Why:** Following approved architecture, Cosmos DB best practices, Python conventions.

### 2026-04-11: Repository pattern — implemented
**By:** Neo (proposal) + Morpheus (implementation)
**What:** Full repository layer separating data access from business logic. 4 Protocol interfaces (Transaction, ReferenceItem, Category, Audit). Cosmos implementations in repositories/cosmos/. Services now take repository dependencies via constructor injection. FastAPI DI for singleton repos.
**Why:** Services were tightly coupled to Cosmos SDK. Repository pattern enables testability and future DB swaps.

### 2026-04-12: Security scan completed — 33 findings
**By:** Neo, Morpheus, Trinity, Tank (scan) + Switch (expert review)
**What:** Full-stack security audit: 5 CRITICAL, 11 HIGH, 10 MEDIUM, 7 LOW. Top priorities: remove COSMOS_KEY from CI, Cosmos DB hardening, file upload validation, CORS restrictions, JWT error leakage.
**Report:** docs/security/scan-2026-04-12.md
**Lesson:** Security scans must include domain expert from the start.

### 2026-04-12: V2 revamp — implementation phasing
**By:** Pedro (user directive)
**What:** V2 structured in 4 phases by dependency order:
- Phase 1 — Core data model + CRUD (transaction type enum, new fields, manual CRUD)
- Phase 2 — Import improvements (Bank mode, Inline mode, uncategorized support)
- Phase 3 — Split transactions (FR-022–025)
- Phase 4 — Smart categorization (FR-019, FR-020)
**Why:** Core model must be solid before building features on top.
### 2026-04-14: Product renamed — "NGO Treasury" → "OpenTreasury"
**By:** Oracle (Docs), Trinity (Frontend), Morpheus (Backend), requested by Pedro
**What:** All user-facing text renamed from "NGO Treasury" / "ngo-treasury" to "OpenTreasury" / "opentreasury" across docs (13 files), frontend code (package.json, angular.json, localStorage keys), and backend config (config.py default, logger name, .env examples). Azure resource names (`rg-ngo-treasury-*`, `cosmos-ngo-treasury-*`, etc.) and generic NGO references intentionally preserved.
**Why:** Product identity change requested by Pedro.

### 2026-04-14: Cosmos DB default database name changed to "opentreasury"
**By:** Morpheus (Backend Dev), requested by Pedro
**What:** `COSMOS_DATABASE_NAME` default in `config.py` changed from `ngo-treasury` to `opentreasury`. Existing deployments must set `COSMOS_DATABASE_NAME=ngo-treasury` in environment or rename/recreate the database. `api/tests/conftest.py` Entra audience (`api://ngo-treasury-api`) unchanged until infra is re-provisioned.
**Why:** Aligns backend default with new product name.
### 2026-04-14: Infra naming — 3-tier strategy
**By:** Neo (Lead), requested by Pedro
**What:** Infra `ngo-treasury` references classified into three tiers:
- **Do Now:** Change main.bicep default, parameterize cosmos-db.bicep + app-service.bicep database names, regenerate main.json, update scripts + docs. Zero deployment risk — Bicep only runs when explicitly triggered.
- **Do When Reprovisioning:** Pedro's `.azure/config`, Cosmos DB database rename (no in-place rename), Entra ID app registration URI (`api://ngo-treasury-api`).
- **Do Never:** Redeploy existing prod with `projectName = 'opentreasury'` without migration planning — would create new resources and orphan old ones.
**Why:** Azure resource names are baked into DNS/connection strings. Code/docs should reflect `opentreasury` for fresh deployments; existing resources stay as-is until reprovisioned.

### 2026-04-14: Infra parameterized — hardcoded database names removed
**By:** Tank (DevOps), requested by Pedro
**What:** `cosmos-db.bicep` and `app-service.bicep` now accept database name as a parameter wired from `main.bicep` via `projectName`. Default `projectName` changed to `opentreasury`. Scripts and docs updated accordingly.
**Why:** OpenTreasury is org-agnostic. Database names must be parameterized so per-org deploy repos can override defaults.
**Impact:** `main.json` must be regenerated after Bicep changes. Existing deployments using `ngo-treasury` continue working if they pass `projectName: 'ngo-treasury'` explicitly.

### 2026-04-14: Org-agnostic posture confirmed
**By:** Pedro (user directive)
**What:** The public OpenTreasury repo must contain zero org-specific references. No "Rett Spain", no hardcoded database names, no deployment config. Each deploying org has a separate private repo for deployment configuration (bicepparam overrides, workflows, secrets).
**Why:** Multi-org product — same codebase, different deployments per NGO.

### 2026-04-12: No backward compatibility — clean break
**By:** Pedro (user directive)
**What:** V2 is a clean break. No deprecated endpoints, no backward-compatible shims, no legacy aliases. Old code gets deleted, not kept around.
**Why:** Small team, no external consumers. Maintaining deprecated code is waste.

### 2026-04-12: Phase 1 spec — architectural decisions resolved
**By:** Niobe (Spec / UX Analyst)
**What:**
1. TransactionType COEXISTS with CategoryType — transactionType determines amount sign, categoryType provides structural classification.
2. Nullable categoryId (option a) — no fake "Uncategorized" category. categorizationStatus enum tracks state.
3. Flexible review status (pending/reviewed/approved/flagged) — any-to-any transitions, no strict state machine.
4. TransactionType enum: income, expense, transfer, refund (no adjustment in Phase 1).
5. Correction tracking: write-once originalAmount/originalDate on first edit.
6. Reports switch to transactionType-based classification — transfers/refunds excluded from income/expense totals.
**Spec:** docs/specs/phase-1-core-model-spec.md

### 2026-04-13: Design token system implemented
**By:** Mouse (UI Designer)
**What:** Complete design token system: `_tokens.scss` (200+ CSS custom properties), `_breakpoints.scss` (responsive mixins), `styles.scss` rewritten to use zero hardcoded values, `custom-theme.scss` dark theme.
**Why:** Foundation for consistent UI. Eliminates ad-hoc values, enables dark mode, fixes WCAG contrast issues.

### 2026-04-13: Repo strategy — public product + private deployment
**By:** Pedro (user)
**What:** Two-repo architecture: `rett-europe/opentreasury` (public product code) + private per-org deployment repos (workflows, parameters, secrets). Product repo has no org-specific config. Deployment repos check out the product repo and overlay org config.
**Why:** Multi-org support — same product, different deployments per NGO.

### 2026-04-14: Trunk-based development — branching policy
**By:** Pedro (user directive)
**What:** All new features and fixes must be on separate branches. Use trunk-based development: commit on feature/fix branches, open pull requests to merge into main. No direct commits to main.
**Why:** User request — captured for team memory.

### 2026-04-14: Deploy template spec — architectural decisions
**By:** Neo (Lead/Architect)
**Status:** Superseded by the agreed architecture in "Deploy template — DevOps review" and "Deploy template — security review" below.
**What:**
1. Deploy template includes **3 files** (deploy.yml + deploy-infra.yml + README) — product repo has all infra/code
2. **Standalone `deploy-infra.yml`** for first-time bootstrap and infra-only changes (least-privilege separation)
3. **No prod.bicepparam in deploy repo** — `using` path creates fragile cross-repo dependencies; params passed inline
4. **1 secret + 8 variables** (not 12) — OIDC federation, Key Vault refs + Managed Identity eliminate persistent credentials
5. **Manual workflow_dispatch only** for v1 — adopters control when to pull new product versions
6. **Zip deploy** (not container) for v1 — matches existing `WEBSITE_RUN_FROM_PACKAGE=1` + `startup.sh` pattern
**Why:** Simplest version that works with security-first posture. Don't duplicate what the product repo already provides.
**Spec:** docs/specs/deploy-template-spec.md

### 2026-04-14: Deploy template — DevOps review
**By:** Tank (DevOps)
**What:**
1. **3-job workflow** correct: `deploy-infra` → (`deploy-backend` + `deploy-frontend`) in parallel
2. **Standalone deploy-infra.yml** — yes, keep separate for first-time bootstrap and infra-only changes
3. **Checkout layout**: deploy repo at root, product repo as subdirectory pinned to release tag
4. **Secrets reduced to 6 + 3 variables**: eliminated COSMOS_KEY (managed identity) and COSMOS_ENDPOINT (Bicep-wired)
5. **Key Vault RBAC propagation delay** (5-10 min) — first deploy needs health-check retry step
6. **Frontend env injection**: `sed` placeholder replacement in `environment.prod.ts` before `ng build`
**Why:** Practical DevOps validation of the spec.

### 2026-04-14: Deploy template — security review
**By:** Switch (Security Engineer)
**What:**
1. **Only 1 real GitHub Secret** (`AZURE_STATIC_WEB_APPS_API_TOKEN`). All others are Variables or eliminated.
2. **OIDC federation is mandatory** — replaces `AZURE_CREDENTIALS` persistent SP credential. Short-lived tokens (5-10 min) instead of 1-year client secrets.
3. **COSMOS_KEY must not be a GitHub Secret** — flagged as C4 in April 12 scan. App uses managed identity at runtime.
4. **Secret classification**: 1 secret + 8 variables + 3 eliminated (from original 12).
5. **NGO fork caveat**: OIDC federated credential `subject` claim must match the deploying org's repo name.
**Why:** Security-first review. Persistent credentials are unacceptable risk for NGO adopters.

### 2026-04-14: Mandatory branch enforcement — coordinator must branch before spawning
**By:** Pedro (user directive)
**What:** ALL work MUST go on feature branches. Never commit directly to main. The coordinator must create a feature branch BEFORE spawning any agents that produce artifacts. This is trunk-based development — all changes go through PRs. Learned the hard way: spec commit went to main (2026-04-14).
**Why:** Spec work was committed directly to main instead of a branch. Pedro caught it.

### 2026-04-14: Security expert (Switch) has final say — non-negotiable
**By:** Pedro (user directive)
**What:** On all security-related decisions, Switch's opinion is authoritative and non-negotiable. The team must always adopt the most secure option. For the deploy-template this means: OIDC federation (no persistent SP secrets), COSMOS_KEY eliminated (Managed Identity only), config values → GitHub Variables, Cosmos DB `disableLocalAuth: true`, Key Vault `enablePurgeProtection: true`, AZURE_CLIENT_ID naming conflict resolved, GitHub Actions pinned to SHA with explicit permissions blocks.
**Why:** "This needs to be a top solution from security perspective, not negotiable, so the security expert opinion will always win."

### 2026-04-14: Deploy template spec v2 — Neo answers Pedro's 4 questions
**By:** Neo (Lead/Architect)
**What:**
1. **Why wasn't Niobe involved?** Neo acknowledges the oversight — specs need requirements/UX review, not just architecture. Going forward, ALL specs (including Lead-authored) get a Niobe review pass before merge.
2. **Versioning:** GitHub Releases with semantic versioning. Tags are immutable. Adopter sets `product_ref: v1.2.0` in workflow dispatch. Changelog via `gh release create --generate-notes`.
3. **Full lifecycle:** Discovery → Provisioning (~30 min claimed) → Day-2 ops → Upgrading → Troubleshooting. Persona-aware: NGO admin, not a developer.
4. **Switch's security requirements:** All adopted. OIDC federation, COSMOS_KEY eliminated, 1 secret + 8 variables, Cosmos `disableLocalAuth`, Key Vault `enablePurgeProtection`, Actions pinned to SHA. Switch has final say — team policy.
**Also adopted from Tank:** Separate `deploy-infra.yml`, sed-before-build for frontend tokens, RBAC propagation delay + health check retry.
**Process decisions:** Niobe reviews all specs (no exceptions). All work on feature branches. Switch's authority on security is absolute.
**Spec:** docs/specs/deploy-template-spec.md (v2)

### 2026-04-14: Deploy template — adopter experience review (14 recommendations)
**By:** Niobe (Spec / UX Analyst)
**What:** Full adopter journey analysis. Defined realistic persona ("Ana" — NGO IT contact, not a DevOps engineer). Mapped 7-stage lifecycle from discovery to ongoing operations. Reality-checked the "30 minutes" claim (actual: 60-90 min for deployment, 2-3 hours from "I want to try" to "first spreadsheet imported"). Identified 7 spec gaps:
1. **No post-deployment onboarding** (Entra role assignment, first-use setup) — HIGH
2. **No error recovery guidance** (adopters afraid to re-run scripts) — HIGH
3. **Windows/PowerShell is second-class** (only bash mentioned) — MEDIUM
4. **No cost transparency at decision time** (€15-25/month breakdown needed) — MEDIUM
5. **No "is my deployment healthy?" checklist** — MEDIUM
6. **MSAL_API_SCOPE naming mismatch** between script output and GitHub secrets — MEDIUM
7. **No Entra ID tier requirements documented** (P1 needed for group-based roles?) — HIGH
**Key recommendations:** Define adopter persona in README, revise time claim to ~1 hour, add cost breakdown, make PowerShell first-class, default `product_ref` to latest release tag (not `main`), add version badge in app footer, add plain-language changelogs.
**Assessment:** Spec is technically solid but written by engineers for engineers. Biggest adoption risks are non-technical: the gap between deployment and first use, the versioning story, and no error recovery.

### 2026-04-14: AZURE_CLIENT_ID → ENTRA_API_CLIENT_ID rename (backend)
**By:** Morpheus (Backend Dev)
**What:** Renamed `AZURE_CLIENT_ID` to `ENTRA_API_CLIENT_ID` in all backend Python code and .env example files (config.py, auth/dependencies.py, conftest.py, .env.example, .env.cosmos-emulator.example). This is the API app registration client ID used for Entra ID audience validation — distinct from the `AZURE_CLIENT_ID` that `DefaultAzureCredential` auto-discovers for managed identity.
**Why:** Per deploy-template-spec §4.5 — `DefaultAzureCredential` consumes `AZURE_CLIENT_ID` for managed identity auth. Reusing the same env var for the API audience registration caused a collision. The new name `ENTRA_API_CLIENT_ID` is unambiguous.
**Scope:** Backend only. Bicep/workflows/scripts are Tank's responsibility.

### 2026-04-14: Deploy template implementation — Bicep hardening + workflows
**By:** Tank (DevOps)
**What:**
1. **Bicep hardening applied:** `disableLocalAuth: true` on Cosmos DB (forces Managed Identity, eliminates COSMOS_KEY attack vector), `enablePurgeProtection: true` on Key Vault (prevents permanent secret deletion).
2. **AZURE_CLIENT_ID → ENTRA_API_CLIENT_ID rename:** Updated in key-vault.bicep (secret name) and app-service.bicep (app setting + KV reference). Eliminates collision with DefaultAzureCredential's AZURE_CLIENT_ID.
3. **deploy-infra.yml passes azureClientId from vars.MSAL_CLIENT_ID:** The API app registration client ID is needed as a Bicep @secure() param for the Key Vault secret.
4. **setup-python action added to deploy.yml:** SHA-pinned actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 (v5.6.0) for Python 3.12 in the API build step.
5. **main.json regenerated** after all Bicep changes — clean, zero diagnostics.
**Why:** Per deploy-template-spec.md §4.3, §4.5, §5.1, §5.2. Security hardening endorsed by Switch.

### 2026-04-14: Script output must match README's GitHub config table
**By:** Niobe (Spec / UX Analyst)
**What:** The setup scripts (`setup-azure.sh` and `setup-azure.ps1`) still print a legacy GitHub Secrets table that includes `AZURE_CREDENTIALS` and doesn't distinguish Secrets vs Variables. The deploy-template README documents the spec's correct classification: 1 GitHub Secret (`AZURE_STATIC_WEB_APPS_API_TOKEN`) + 8 GitHub Variables. The scripts need updating so their output matches the README 1:1.
**Why:** Adopter UX — script output is the single source of truth during provisioning. Mismatch causes confusion.
**Action needed:** Update Step 9 output in both scripts to print two separate tables (Secrets and Variables), matching the exact names documented in the README.

### 2026-04-18: System Settings (Issue #12) — main-alignment decisions

**By:** Neo (Lead / Architect)
**What:** Implementation of the approved System Settings spec needs three precision amendments to land cleanly on main as it stands today (Balance section, Date range filter, Split transactions, and auth refactor `cab41d5` all merged after spec approval). Spec core is intact — these clarify rendering rules.
- **A3 — Date format token mapping table.** Persisted tokens (`DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`, `DD MMM YYYY`) → Angular `DatePipe` patterns (`dd/MM/yyyy`, `MM/dd/yyyy`, `yyyy-MM-dd`, `dd MMM yyyy`). Centralised in a single `DateFormatPipe` in `core/pipes/`. Owners: Trinity, Cypher.
- **A4 — Export filenames always ISO `YYYY-MM-DD`** regardless of the `dateFormat` setting. The display preference must not bleed into filenames (avoids `/` and spaces breaking Windows/macOS). Owners: Trinity (frontend), Morpheus (any backend-built filenames).
- **A5 — Currency pipe call shape standard.** All Angular currency pipes use `currency : codeSignal() : 'symbol' : '1.2-2'` (four arguments). Owners: Trinity, Cypher.

**Bootstrap mechanism for A2:** `APP_INITIALIZER` in `app.config.ts`, with a 1.5 s timeout inside `SystemSettingsService.load()` to fall back to defaults rather than stall app boot.

**Cosmos container:** Reuse existing `reference_data` container with `id="system"`, `partitionKey="system_settings"`. Saves RU floor cost vs a new `system_config` container; consistent with `accounts`/`tags` precedent.

**Affects:** Trinity, Morpheus, Cypher, Switch.
**Companion docs:** `docs/specs/system-settings-main-alignment-delta.md`, `docs/specs/system-settings-frontend-scoping.md`, `docs/specs/system-settings-backend-scoping.md`, `docs/specs/system-settings-security-review.md`.

### 2026-04-18: System Settings — admin-only PUT enforcement (security)

**By:** Switch (Security Engineer)
**What:**
- `PUT /api/settings` MUST use `Depends(get_current_admin)`; `GET /api/settings` MUST use `Depends(get_current_user)` (any authenticated user — viewers need currency/date format to render the app).
- `updatedBy` MUST be the JWT `oid` claim, never client-supplied. `updatedAt` MUST be the server clock in UTC ISO 8601, never client-supplied.
- The Pydantic update DTO MUST use `model_config = ConfigDict(extra="forbid")` to reject any client-supplied audit fields with HTTP 422 (defense-in-depth layer 1). The service MUST also overwrite `updated_at` and `updated_by` from server-supplied parameters (defense-in-depth layer 2).

**Why:** Frontend `adminGuard` is a UX convenience; the backend is the enforcement boundary. A1 requires server-authoritative audit fields; the two-layer defense ensures the audit trail cannot be poisoned even if the schema were ever loosened. Auth refactor `cab41d5` is security-positive (removed dev-mode mock); no regression to existing admin model.
**Sign-off conditions:** the 10 MUSTs in `docs/specs/system-settings-security-review.md` §6, with corresponding tests, plus clean lint/format.
**Affects:** Morpheus (backend implementation + tests), Trinity (frontend route + sidenav guard), Cypher (test coverage).

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
