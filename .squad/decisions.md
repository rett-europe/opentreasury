# Squad Decisions

## Active Decisions

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

### 2026-04-18: Phase B kickoff — data-mapping contract (B-1)
**By:** Neo (Lead/Architect)
**What:** SQLite repositories own the bidirectional mapping between SQL row-tuples (snake_case columns per `app/repositories/sqlite/schema.py`) and the Cosmos-shaped `dict` documents that services already consume (camelCase: `partitionKey`, `accountId`, `categoryId`, `subcategoryId`, `transactionType`, `tagIds`, `splitLines`, `isSplit`, `isDeleted`, `bankDescription`, `detail`, etc.). Each SQLite repo gets exactly one private `_to_doc(row) -> dict` and one `_from_doc(doc) -> dict` helper — no mapping logic scattered through methods. Service and router files are not touched.
**Why:** Option (b) — "move services to a canonical shape" — would touch every service and router, breaking layering for a backend-swap concern. Option (a) keeps the swap surface inside the repository tier where it belongs (spec §4.1, §4.3). The Cosmos-document shape becomes the de facto canonical contract because (1) every service already speaks it, (2) every API response already serializes it, (3) the existing service test suite asserts against it, and (4) it's what the Cosmos repo emits unchanged. SQLite is the new adapter; it adapts to the existing contract, not the other way round.
**Implications:**
- Mapping is the *only* place column-name divergence is allowed. If a parity test fails because a service reads `doc["isSplit"]`, the fix is in `_to_doc`, never in the service.
- `Decimal` discipline preserved at the mapping boundary: `aiosqlite` returns `NUMERIC` as strings; `_to_doc` wraps in `Decimal`, `_from_doc` accepts `Decimal | str | int | float` and stores canonically.
- Soft-delete invariant: `_to_doc` always emits `isDeleted: bool`; read paths filter `is_deleted = 0` in SQL unless `include_deleted=True`.
- JSON columns (`tags`, `notes`, `subcategories`, `attributes`, `split_lines`) round-trip through `json.loads`/`json.dumps` in the mapping helpers; services never see raw JSON strings.
**Scope:** Applies to all five SQLite repos (transactions, categories, reference_item, audit, user_preferences) for PRs B.4–B.7.

### 2026-04-18: Phase B schema-gap list — migration `0002_phase_b_schema_parity` (B-2)
**By:** Neo (Lead/Architect), with Morpheus gap analysis against Cosmos repo + service layer
**What:** Migration `0002_phase_b_schema_parity` (Morpheus owns in PR B.2) closes the gaps between `schema.py` v1 (Phase A) and the fields that existing services and the Cosmos repo actually read/write. The exact gap inventory:

| # | Add to `transactions` | Type | Why |
|---|---|---|---|
| 1 | `is_split` | `Integer NOT NULL DEFAULT 0` | Read by `query_for_report` and `aggregate_filtered`; differentiates split parents from leaf transactions when counting "uncategorized." |
| 2 | `split_lines` | `JSON NULL` | Embedded split-line array (Phase 3 decision, 2026-04-14). Without it `query_for_report` cannot unroll splits and reports diverge from Cosmos. |
| 3 | `bank_description` | `Text NULL` | Half of the `search` filter target in `_build_filter_conditions`. Currently the schema has only `description` (which maps to `detail`). Both fields must exist for parity. |
| 4 | `detail` | `Text NULL` | Other half of the `search` filter. Distinct from `description` in the Cosmos document. |
| 5 | `reviewed_by_email` | `String NULL` | Stamped by the review service alongside `reviewed_by` and `reviewed_by_name`. Missing in v1. |
| 6 | `tag_ids` | `JSON NULL` | Renamed from v1's `tags` for explicit parity with Cosmos `tagIds`. The `count_by_tag` query uses `ARRAY_CONTAINS(c.tagIds, …)`; the SQLite equivalent uses `json_each(tag_ids)`. v1's `tags` column is dropped (Phase A had no production data). |

| # | Other tables | Change | Why |
|---|---|---|---|
| 7 | `categories` | Confirm `subcategories` JSON shape matches `[{id, name, sortOrder?}]` documented by Cosmos repo | No structural change; assertion-only test |
| 8 | `audit_log` | Add nullable `metadata` JSON column | Used by audit service for free-form context; present in Cosmos documents |

**Out of scope for B.2** (deferred to Phase D per plan §4):
- `version` column wiring for optimistic concurrency (column exists from Phase A; the *behavior* lands in Phase D).
- Any FK constraints between `transactions` and `categories`/`reference_data` — Cosmos doesn't enforce them, parity says SQLite shouldn't either; integrity stays at the service tier.
- `app_identity` / `users` changes — Phase C surface.

**Why:** Defining the gap list as a decision (not just a Morpheus PR) means parity tests in B.3 can assert against a fixed contract. Without this fixed list, scope-creep on B.2 is guaranteed.

### 2026-04-18: Phase B Electron shell technology choices (B-4)
**By:** Neo (Lead/Architect), with Trinity (shell), Tank (packaging), Switch (security gate)
**What:**
1. **Builder:** `electron-builder` (not `electron-forge`). Reasons: (a) first-class Windows/macOS installer support needed in Phase E with one config; (b) Tank's existing GitHub Actions experience with build/sign pipelines maps directly; (c) `electron-forge` adds a templating layer we don't need around a single Angular app.
2. **Dev workflow:** Electron main loads `http://localhost:4200` in dev (Angular `ng serve`), and the packaged `file://dist/...` URL in prod. No webpack-dev-server middleware in Electron itself — keeps the shell dumb.
3. **FastAPI sidecar supervision:** Electron main process spawns the Python sidecar as a child process via `child_process.spawn`, with: ephemeral port allocation (probe-and-bind starting at 8765), stdout/stderr piped to Electron's log file (`app.getPath('logs')`), `SIGTERM` on Electron `before-quit` with a 5s grace period before `SIGKILL`. The sidecar entrypoint is a new `api/desktop_main.py` (PR B.8) that reuses `app.main:app` — no router/service changes.
4. **Renderer ↔ API transport:** **HTTP-only over `127.0.0.1:<port>`.** No Electron IPC for data, no `contextBridge` exposure of database handles, no `nodeIntegration`. The renderer is treated as untrusted code talking to a localhost service — same posture as the cloud build. Switch sign-off: this is the only acceptable posture (spec §8.5; Switch authority team policy 2026-04-14).
5. **Port discovery:** Main process writes the bound port to a tiny preload-injected global (`window.__OT_API_BASE__`) read once at Angular bootstrap. No port hardcoding in Angular environment files for desktop builds.
6. **Workspace location:** New top-level `desktop/` directory (sibling of `frontend/`, `api/`), not nested under `frontend/`. Reason: it's a deployment shell, not a frontend artifact; nesting confuses build paths and `npm` workspace boundaries.
7. **What B.8 ships:** `desktop/package.json`, `desktop/main.js` (or `.ts`), `desktop/preload.js`, `npm run desktop:dev` script that launches sidecar + `ng serve` + Electron in the right order. **No installer config** (that's Phase E). **No MSAL/Graph/identity code** (that's Phase C).

**Why:** Locks the shell architecture before Trinity/Tank touch it, so PR B.8 reviews are about correctness, not architecture. Switch's HTTP-loopback-only call is the most important constraint and it's non-negotiable.

### 2026-04-18: Phase B.8 + B.9 work distribution
**By:** Neo (Lead/Architect)
**What:** B.0–B.7 are merged (PRs #15, #18). The remaining Phase B slices are B.8 (Electron shell + local FastAPI sidecar) and B.9 (desktop dev runbook). B.8 is multi-owner and is therefore sub-sliced; each sub-slice has exactly one owner, an explicit deliverable, machine-checkable acceptance criteria, and a reviewer gate. The architecture is already locked by decision B-4 (2026-04-18) — these packets implement that decision, they do not redesign it.

#### B.8 sub-slices

| ID | Owner | Deliverable | Acceptance criteria | Depends on |
|----|-------|-------------|---------------------|------------|
| **B.8a** | Morpheus | `api/desktop_main.py` — sidecar entrypoint that imports `app.main:app`, sets `DATA_BACKEND=sqlite`, resolves `SQLITE_DB_PATH` from CLI arg or env, binds `127.0.0.1` on an ephemeral port via `uvicorn.Config(host="127.0.0.1", port=0)`, and prints exactly one parseable line `OT_API_PORT=<port>\n` to stdout once the bind succeeds. | (1) `python -m app.desktop_main --db /tmp/x.sqlite` boots, prints the port line within 5s, serves `/health` 200; (2) binds `127.0.0.1` only — `0.0.0.0` bind is rejected by a unit test that inspects the `Config`; (3) no router/service edits in this PR; (4) lint + black + pytest green per the 2026-04-12 enforcement decision. | B-4 (locked) |
| **B.8b** | Trinity | `desktop/` workspace skeleton: `package.json` (electron + electron-builder dev deps only — no installer config), `main.js`, `preload.js`. `BrowserWindow` with `nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`. Loads `http://localhost:4200` when `NODE_ENV=development`, else `file://` of the packaged Angular `dist/`. | (1) `cd desktop && npm install && npm run start:shell` opens an Electron window pointed at `http://localhost:4200` (assumes `ng serve` already running — orchestration is B.8e); (2) DevTools shows the three security flags above as `true` in `process.argv` / window prefs; (3) no Python or sidecar logic in this PR. | B-4 (locked) |
| **B.8c** | Trinity, **Switch security gate** | Sidecar lifecycle in `desktop/main.js`: `child_process.spawn` of B.8a, parse `OT_API_PORT=<port>` from stdout (regex anchored line-start), pipe stdout/stderr to `app.getPath('logs')/sidecar.log`, on `app.on('before-quit')` send `SIGTERM` then `SIGKILL` after 5s grace. Inject the resolved base URL `http://127.0.0.1:<port>` into the renderer via `preload.js` as `window.__OT_API_BASE__` (frozen string). | (1) Killing Electron leaves no orphan Python process (verified by ps grep in a CI smoke job on Linux runner); (2) port is read from the spawned process — no hardcoded port anywhere; (3) preload exposes only the base-URL string via `contextBridge.exposeInMainWorld`, nothing else; (4) Switch checklist (B.8f) signed off before merge. | B.8a, B.8b |
| **B.8d** | Trinity | Angular bootstrap reads `window.__OT_API_BASE__` once in `app.config.ts` (or equivalent provider) before the HTTP client is constructed, and uses it as the API base. Web build falls back to `environment.apiBase` unchanged. | (1) Web `ng build --configuration=production` output is byte-identical for unrelated chunks (no behavior change for cloud build); (2) when `window.__OT_API_BASE__` is set, every outbound request in DevTools goes to that origin; (3) no HTTP interceptor — base URL is set at construction time. | B.8c |
| **B.8e** | Tank | Top-level `npm run desktop:dev` script that orchestrates: `ng serve` → wait until `http://localhost:4200` responds → launch Electron (which spawns the sidecar). Cross-platform (Windows / macOS / Linux). May add at most one new dev dependency for the wait step (e.g. `wait-on`); justify in the PR. | (1) Single command bring-up on a clean clone after `npm install` in both `frontend/` and `desktop/` and `pip install -r api/requirements.txt`; (2) Ctrl-C tears down all three processes cleanly; (3) documented preconditions match B.9 runbook exactly. | B.8a, B.8b, B.8c, B.8d |
| **B.8f** | Switch | One-page security checklist `docs/security/desktop-shell-checklist.md` asserting and signing off: bind `127.0.0.1` only; no `nodeIntegration`; `contextIsolation: true`; `sandbox: true`; preload exposes only `__OT_API_BASE__` (no DB handles, no fs, no shell); CSP for the `file://` prod load; no `--remote-debugging-port` in prod; sidecar stderr does not leak secrets. | Checklist file merged with Switch as the commit author or reviewer-of-record. **Blocks B.8c merge.** | B.8b, B.8c |
| **B.8g** | Cypher | `tests/desktop/test_sidecar_smoke.py` — pytest that subprocess-launches `api/desktop_main.py` against a temp SQLite path, parses the port line, hits `/health`, creates one transaction, lists it, soft-deletes it, asserts list excludes it. No Electron required — exercises the contract that B.8c depends on. | (1) Test passes against the merged B.8a sidecar; (2) test fails loudly (not flakily) if the port-line contract changes; (3) added to the existing `pytest tests/` invocation, not a new test runner. | B.8a |

#### B.9

| ID | Owner | Deliverable | Acceptance criteria | Depends on |
|----|-------|-------------|---------------------|------------|
| **B.9** | Oracle | `docs/guides/desktop-dev.md` — developer runbook covering: prerequisites (Node 20.x LTS, Python 3.12, the two `npm install` + one `pip install`), the single `npm run desktop:dev` command, log file locations (Electron logs path + `sidecar.log`), and a troubleshooting table (port collision, sidecar crash, stale SQLite, "I see the cloud UI not the desktop UI"). Cross-references spec §9 (Phase B), B-4 decision, and the B.8 PR. | (1) A teammate who has not touched the codebase can go from `git clone` to a working desktop window using only this guide; (2) no commands in the guide differ from what `npm run desktop:dev` actually runs; (3) Oracle adds a one-line entry to `docs/features.md` deferring the user-facing desktop feature note to Phase C (per spec §11). | B.8e merged |

#### Recommended PR slicing for the Coordinator

1. **PR B.8.1** — B.8a (Morpheus) + B.8g (Cypher). Mergeable independently; unblocks every other slice.
2. **PR B.8.2** — B.8b + B.8c + B.8d (Trinity) + B.8e (Tank). Single PR because the four slices are tightly coupled and a partial merge ships a non-bootable shell. Switch reviews B.8f as a blocking review on this PR; if Switch requires changes, those land in the same PR — do not split into a separate "hardening" PR.
3. **PR B.9** — Oracle. Strictly follows PR B.8.2.

**Reviewer gates (every PR):**
- **Neo:** architectural drift from B-4 only. If a reviewer comment from Neo is "this is fine but I'd do it differently," it is not a change request.
- **Switch:** mandatory blocking review on PR B.8.2.
- **Tank:** cross-platform CI gate on PR B.8.2 (must run on at least one Linux runner; Windows/macOS deferred to Phase E).
- **Cypher:** smoke test must remain green; any new desktop-only test must not be skipped on the cloud CI matrix.

**Out of scope, do not let scope-creep in:**
- Installer / code-signing / auto-update — Phase E.
- MSAL, Graph, OneDrive picker, mode-selection screen, identity chip — Phase C, blocked on Niobe's NGO UX validation (spec §12 Q3–Q8).
- Advisory locks, conflict UX, encryption-at-rest decision — Phase D, blocked on Switch (§12 Q1) and the concurrency target (§12 Q2).

**Neo reopens when:** (a) any owner raises an architectural question not answered by B-4 or this distribution; (b) Switch's checklist surfaces a posture conflict the spec doesn't already resolve; (c) all of B.8 + B.9 is merged — Neo then opens Phase C kickoff after Niobe's UX validation lands. Otherwise Phase B routes through the named owners directly, not through Neo.

**Why:** Phase B's architectural decisions (B-1, B-2, B-4) and the spec amendment (§4.3.1, §4.3.2) are merged. The remaining work is implementation against a frozen contract. Neo's charter (`I don't handle: direct implementation of UI components / API endpoint coding / test writing`) routes that work to Trinity, Morpheus, Tank, Cypher, Switch, and Oracle. Distributing it explicitly — with one owner per packet, machine-checkable acceptance criteria, and a fixed reviewer matrix — is the Lead-shaped action and prevents the failure mode where "the Lead said proceed" gets read as "the Lead will write it."

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
