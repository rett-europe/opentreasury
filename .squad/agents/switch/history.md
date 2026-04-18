# Switch — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Deploy Template Security Review
- Reviewed the 12-secret reference list for Neo's deploy-template spec. Only 1 is a true secret (SWA API token). 8 are config values (should be GitHub Variables). 3 should be eliminated (AZURE_CREDENTIALS → OIDC, COSMOS_KEY → Managed Identity, COSMOS_ENDPOINT → Bicep output).
- OIDC federation is a must-have, not optional. AZURE_CREDENTIALS is a permanent SP credential with 1-2yr expiry — OIDC tokens last 5-10 minutes.
- Key security concern: `AZURE_CLIENT_ID` env var naming conflict between Entra app registration (JWT audience) and DefaultAzureCredential (MI identification). This is how COSMOS_KEY accidentally stays in use. Template must resolve naming.

### 2026-04-18: System Settings (Issue #12) — admin-only PUT review
- **Re-validating auth after a refactor:** any commit touching `app/services/dependencies.py` or `app/auth/` requires re-confirming that `get_current_admin` is still the canonical admin gate and is wired in every admin-only router. `cab41d5` removed dev-mode mock auth — security-positive. No regression. Read every router that needs admin-only enforcement to confirm `Depends(get_current_admin)` is applied; never accept a manual `if user["role"] == "Admin"` check.
- **A1 enforcement (server-authoritative audit fields):** two layers of defense always — Pydantic `extra="forbid"` rejects client-supplied audit fields with 422 before the handler runs; service-side override stamps `updated_at` and `updated_by` from server-supplied parameters even if the schema were loosened. Use Entra `oid` (immutable) as the primary identifier, optionally store `name` as readable secondary.
- **GET endpoints for non-secret config should NOT be admin-only.** Currency code and date format are needed by viewers to render the app correctly. Add an inline comment on the GET handler explaining why, so future maintainers don't tighten it accidentally.
- Gotcha #2 (Bicep appSettings replace-all) is security-relevant: a CI workflow that sets appSettings via `az webapp config appsettings set` will **overwrite** Key Vault references. Template must warn against this pattern.
- Gotcha #3 (WEBSITE_RUN_FROM_PACKAGE read-only filesystem) is actually a security benefit — prevents webshell injection.
- Minimum SP permissions: Contributor + User Access Administrator on RG for v1. Document split-SP approach (infra vs app deploy) for hardening.
- Cosmos DB: `disableLocalAuth: true` + Key Vault `enablePurgeProtection: true` are one-line Bicep fixes that must be in the template.
- Review written to: `.squad/decisions/inbox/switch-deploy-template-security.md`
