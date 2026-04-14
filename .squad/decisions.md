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

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
