# Switch — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Deploy Template Security Review
- Reviewed the 12-secret reference list for Neo's deploy-template spec. Only 1 is a true secret (SWA API token). 8 are config values (should be GitHub Variables). 3 should be eliminated (AZURE_CREDENTIALS → OIDC, COSMOS_KEY → Managed Identity, COSMOS_ENDPOINT → Bicep output).
- OIDC federation is a must-have, not optional. AZURE_CREDENTIALS is a permanent SP credential with 1-2yr expiry — OIDC tokens last 5-10 minutes.
- Key security concern: `AZURE_CLIENT_ID` env var naming conflict between Entra app registration (JWT audience) and DefaultAzureCredential (MI identification). This is how COSMOS_KEY accidentally stays in use. Template must resolve naming.
- Gotcha #2 (Bicep appSettings replace-all) is security-relevant: a CI workflow that sets appSettings via `az webapp config appsettings set` will **overwrite** Key Vault references. Template must warn against this pattern.
- Gotcha #3 (WEBSITE_RUN_FROM_PACKAGE read-only filesystem) is actually a security benefit — prevents webshell injection.
- Minimum SP permissions: Contributor + User Access Administrator on RG for v1. Document split-SP approach (infra vs app deploy) for hardening.
- Cosmos DB: `disableLocalAuth: true` + Key Vault `enablePurgeProtection: true` are one-line Bicep fixes that must be in the template.
- Review written to: `.squad/decisions/inbox/switch-deploy-template-security.md`
