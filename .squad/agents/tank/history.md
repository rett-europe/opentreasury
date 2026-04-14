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
