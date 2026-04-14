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
