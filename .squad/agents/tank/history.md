# Tank — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Infra parameterized — removed hardcoded ngo-treasury
- `cosmos-db.bicep` now accepts `databaseName` as a parameter instead of hardcoding `'ngo-treasury'`.
- `app-service.bicep` now accepts `cosmosDatabaseName` as a parameter for the `COSMOS_DATABASE_NAME` env var.
- `main.bicep` passes `projectName` to both modules. Default changed from `'ngo-treasury'` to `'opentreasury'`.
- `setup-azure.ps1` KV secret now uses `$ProjectName` variable instead of hardcoded string.
- All comments/docs updated from "NGO Treasury" to "OpenTreasury" in task-scoped files.
- `main.json` needs manual regeneration (`az bicep build --file main.bicep`).
- Residual "NGO Treasury" comments remain in: app-insights.bicep, key-vault.bicep, role-assignments.bicep, static-web-app.bicep, setup-azure.ps1 consent strings (lines 162-168). These weren't in scope but should be cleaned up.

### 2026-04-14: Deploy-template DevOps review
- Reviewed full codebase for deploy-template feasibility. Key findings:
- **Secrets audit:** Spec listed 12 secrets; only 6 are actually needed. COSMOS_ENDPOINT is auto-wired via Bicep→KV→App Service KV reference. COSMOS_KEY is not used anywhere (managed identity). AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_WEBAPP_NAME should be GitHub Variables, not Secrets.
- **Bicepparam `using` path:** `../../opentreasury/infra/main.bicep` when deploy repo is root and product repo is checked out to `opentreasury/` subdir. Secure params must be passed via CLI `--parameters`, not in bicepparam.
- **WEBSITE_RUN_FROM_PACKAGE + SCM_DO_BUILD_DURING_DEPLOYMENT conflict:** Both are set in app-service.bicep — they conflict. Recommend CI-installed packages strategy (matches existing startup.sh PYTHONPATH).
- **Key Vault RBAC propagation:** 5-10 min delay after role assignment creation. First-time deploy will see KV 403s. Need health-check retries in workflow.
- **SWA hostname chicken-and-egg:** Frontend build needs SWA URL for MSAL redirects, but hostname is auto-generated on creation. Must pass as job output from deploy-infra to deploy-frontend.
- **Entra app registrations are NOT in Bicep** — adopters must run setup-azure.sh before pipeline works. Critical bootstrap step.
- **Product repo checkout should pin to release tags**, not main HEAD. Prevents upstream breaking changes from hitting production.
- Full review written to `.squad/decisions/inbox/tank-deploy-template-review.md`.

### 2026-04-14: Deploy template implementation
- Created `deploy-template/.github/workflows/deploy.yml` — full code deployment pipeline:
  - OIDC auth (no AZURE_CREDENTIALS), SHA-pinned actions, explicit permissions
  - workflow_dispatch with product_ref input (default 'main')
  - sed-before-build token replacement for MSAL config in environment.prod.ts
  - npm ci + ng build frontend, pip install + zip API
  - az webapp deploy for API, Azure/static-web-apps-deploy for frontend
  - Health check with 3 retries × 60s for RBAC propagation
  - 1 secret (AZURE_STATIC_WEB_APPS_API_TOKEN), 8 vars
- Created `deploy-template/.github/workflows/deploy-infra.yml` — infra deployment:
  - Same OIDC auth + SHA-pinned actions
  - azure/arm-deploy with product/infra/main.bicep, inline params
  - projectName from vars.PROJECT_NAME (default 'opentreasury'), environmentName=prod
  - azureTenantId + azureClientId passed as inline params from vars
- Modified `infra/modules/cosmos-db.bicep`: `disableLocalAuth: true` (Managed Identity only)
- Modified `infra/modules/key-vault.bicep`: added `enablePurgeProtection: true`, renamed secret 'azure-client-id' → 'entra-api-client-id'
- Modified `infra/modules/app-service.bicep`: renamed AZURE_CLIENT_ID → ENTRA_API_CLIENT_ID, updated KV SecretName
- Regenerated `infra/main.json` via `az bicep build`
- Bicep diagnostics: zero errors across all modules
- Key SHAs: checkout@11bd7190 (v4.2.2), azure/login@a457da9e (v2.3.0), arm-deploy@a1361c2c (v2.0.0), static-web-apps-deploy@1a947af9 (v1.0.0), setup-python@a26af69b (v5.6.0)

### 2026-04-16: Cosmos RBAC / COSMOS_KEY cleanup audit — product repo
- Audited 7 files for stale COSMOS_KEY or key-based auth references. **All clean — no changes needed.**
  1. `deploy-template/.github/workflows/deploy.yml` — No COSMOS_KEY or COSMOS_ENDPOINT. Uses OIDC federation.
  2. `deploy-template/.github/workflows/deploy-infra.yml` — No COSMOS_KEY or COSMOS_ENDPOINT. Passes Bicep params only.
  3. `deploy-template/README.md` — Secrets table: 1 secret (SWA token) + 11 variables. No COSMOS_KEY/COSMOS_ENDPOINT.
  4. `infra/modules/app-service.bicep` — COSMOS_ENDPOINT via Key Vault ref. No COSMOS_KEY.
  5. `infra/modules/cosmos-db.bicep` — `disableLocalAuth: true` confirmed.
  6. `scripts/setup-azure.sh` — Summary table clean. No COSMOS_KEY output.
  7. `scripts/setup-azure.ps1` — Summary table clean. Step 7b populates Key Vault with COSMOS_ENDPOINT correctly.
- Bonus: `cosmos_client.py` uses dual-path (key vs DefaultAzureCredential). With `COSMOS_KEY=""` default in config.py, RBAC path is always used in prod. Key param only relevant for Cosmos emulator.
