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
