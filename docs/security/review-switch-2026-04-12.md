# Security Expert Review — Switch Assessment

**Date:** April 12, 2026
**Reviewer:** Switch (Security Engineer)
**Reviewed Report:** `docs/security-scan-2026-04-12.md`
**Original Scanners:** Neo, Morpheus, Trinity, Tank

---

## Executive Assessment

The generalists did solid work — 28 findings, mostly correctly categorized, covering OWASP Top 10 across all layers. However, **they missed a critical dependency vulnerability** (`python-jose==3.3.0` is unmaintained with known issues), **Swagger/OpenAPI is exposed without auth in production**, and the **PR checks silently swallow test failures** (`|| true`). I'm upgrading one finding (H3 → CRITICAL), downgrading two (C1 → HIGH, C6 → HIGH), and adding 5 new findings. The core architecture is sound — the gaps are in hardening, not design.

---

## Finding-by-Finding Assessment

| ID | Finding | Orig. Severity | My Severity | Agree? | Notes |
|----|---------|---------------|-------------|--------|-------|
| C1 | Missing Rate Limiting | CRITICAL | **HIGH** | Partial | All endpoints require JWT. Brute-force threat is low — DoS is real but App Service has some built-in throttling. Not "block production" for a small NGO app behind Entra ID. |
| C2 | Overly Permissive CORS | CRITICAL | CRITICAL | ✅ Yes | `allow_methods=["*"]`, `allow_headers=["*"]` with `allow_credentials=True` is textbook misconfiguration. Origins are controlled via env var which is good, but methods/headers wildcards are the problem. Easy fix. |
| C3 | No CSP (Frontend) | CRITICAL | CRITICAL | ✅ Yes | `staticwebapp.config.json` is bare — just a navigation fallback, zero security headers. No CSP, no X-Frame-Options, no HSTS. Correct severity. |
| C4 | Cosmos DB Local Auth + No Network | CRITICAL | CRITICAL | ✅ Yes | `disableLocalAuth: false` with comment "Keep enabled for portal access" is wrong — Azure Portal works fine with RBAC. No IP firewall or private endpoint means the DB is publicly routable. |
| C5 | COSMOS_KEY in GitHub Actions | CRITICAL | CRITICAL | ✅ Yes | `deploy-prod.yml` L115 explicitly sets `COSMOS_KEY=${{ secrets.COSMOS_KEY }}` via `az webapp config appsettings set`. The Bicep uses Key Vault references correctly, but the CI workflow **overrides** them. Removing the CI setting is the fix. |
| C6 | App Insights Public Access | CRITICAL | **HIGH** | Partial | Misconfigured, but practical risk is telemetry poisoning — not data exfiltration. For an NGO app, this is less impactful than C4/C5. Should still be fixed promptly. |
| H1 | JWT Error Leakage | HIGH | HIGH | ✅ Yes | `detail=f"Token validation failed: {str(last_error)}"` reveals validation internals. Confirmed at `dependencies.py` L107. Fixed with a generic message + server-side logging. |
| H2 | Missing Security Headers (API) | HIGH | HIGH | ✅ Yes | No HSTS, X-Content-Type-Options, X-Frame-Options on API responses. |
| H3 | File Upload Validation Incomplete | HIGH | **CRITICAL** | Upgraded | `application/octet-stream` bypasses all MIME checking. The file bytes go directly to `load_workbook(BytesIO(workbook_bytes))` in import_service.py. openpyxl processes ZIP internally — a crafted file under 10MB can decompress to much more (ZIP bomb). Combined, this is a viable resource exhaustion + potential RCE vector. |
| H4 | JWKS Cache Race Condition | HIGH | HIGH | ✅ Yes | Global mutable `_jwks_cache` / `_jwks_cache_time` without `asyncio.Lock()`. Real issue under concurrent requests during key rotation. |
| H5 | Key Vault No Purge Protection | HIGH | HIGH | ✅ Yes | Soft delete alone isn't enough. One-line fix. |
| H6 | SWA Config File Updates | HIGH | HIGH | ✅ Yes | `allowConfigFileUpdates: true` allows runtime config changes. One-line fix. |
| H7 | Workflow Permissions Not Defined | HIGH | HIGH | ✅ Yes | `deploy-prod.yml` and `deploy-infra.yml` have no `permissions` block — defaults to `write-all`. `pr-checks.yml` also missing, though lower risk. Squad workflows correctly define minimal permissions. |
| H8 | Actions Not Pinned to SHA | HIGH | HIGH | ✅ Yes | All workflows use floating tags (`@v4`, `@v2`, `@v5`, `@v1`). Supply chain risk. |
| H9 | AZURE_CREDENTIALS Not OIDC | HIGH | HIGH | ✅ Yes | Permanent service principal JSON secret. OIDC federation is the standard now. |
| M1 | Tokens in localStorage | MEDIUM | MEDIUM | ✅ Yes | `BrowserCacheLocation.LocalStorage` confirmed. Without CSP (C3), XSS could steal tokens. These are linked — fixing C3 reduces this risk substantially. |
| M2 | No CSRF Protection | MEDIUM | **LOW** | Downgraded | All mutation endpoints require `Authorization: Bearer <jwt>`. CSRF is mitigated by design in token-based APIs. Document the threat model decision and move on. |
| M3 | No Frontend File Validation | MEDIUM | MEDIUM | ✅ Yes | Only `accept=".xlsx"` attribute, easily bypassed. Defense-in-depth — backend validation matters more. |
| M4 | Export Date Range Unbounded | MEDIUM | MEDIUM | ✅ Yes | No `dateFrom <= dateTo` check. No max range. Could trigger expensive Cosmos queries. |
| M5 | Float Arithmetic | MEDIUM | MEDIUM | ✅ Yes | `abs(float(data.amount))` drops Decimal precision. For NGO amounts this is sub-penny variance, but it's poor practice and can accumulate in reports. |
| M6 | Import Auto-Creates Categories | MEDIUM | **LOW** | Downgraded | Requires Admin role. If admins are trusted, this is fine. Document as business logic decision. |
| M7 | App Insights 30-Day Retention | MEDIUM | MEDIUM | ✅ Yes | NGO audit requirements may need longer. |
| M8 | Missing Diagnostic Logging | MEDIUM | MEDIUM | ✅ Yes | No diagnostic settings to Log Analytics on App Service. |
| L1 | Audit TTL Fixed | LOW | LOW | ✅ Yes | |
| L2 | Auth Failure Logging | LOW | **MEDIUM** | Upgraded | Failed auth attempts should be logged for incident detection. Without this, you can't detect credential stuffing or token abuse. Important even for a small app. |
| L3 | Token Validation Retry (4 combos) | LOW | LOW | ✅ Yes | v1/v2 token format complexity is an Entra ID reality. Document expected format. |
| L4 | Frontend Env Config in Source | LOW | LOW | ✅ Yes | Public SPA client IDs are inherently public. Acceptable. |
| L5 | Caret Versioning | LOW | LOW | ✅ Yes | `npm ci` in CI mitigates this. |

---

## NEW Findings (Missed by Original Scan)

### NEW-1. `python-jose==3.3.0` — Unmaintained, Known Issues
- **Severity: HIGH**
- **OWASP:** A06 — Vulnerable and Outdated Components
- **File:** `api/requirements.txt` (L122)
- **Issue:** Production locks `python-jose[cryptography]==3.3.0` (released 2021). The dev requirements pin 3.5.0. The `python-jose` library is **effectively unmaintained** — the last release was 2021 and the repo has unmerged security patches. Known issues include algorithm confusion attacks when using ECDSA.
- **Fix:** Migrate to `PyJWT[crypto]` (already a transitive dep at 2.12.1) or `joserfc`. The app already has PyJWT installed via MSAL — consolidate on one JWT library.

### NEW-2. Swagger/OpenAPI Exposed in Production Without Auth
- **Severity: MEDIUM**
- **OWASP:** A05 — Security Misconfiguration
- **File:** `api/app/main.py` (L37-38)
- **Issue:** `docs_url="/api/docs"` and `openapi_url="/api/openapi.json"` are always active. Anyone can browse the full API schema, including all endpoint paths, parameter names, and response models. This gives attackers a complete reconnaissance map.
- **Fix:** Conditionally disable in production:
  ```python
  docs_url="/api/docs" if not settings.is_production else None,
  openapi_url="/api/openapi.json" if not settings.is_production else None,
  ```

### NEW-3. PR Checks Silently Swallow Test Failures
- **Severity: MEDIUM**
- **OWASP:** N/A — CI/CD Quality Gate
- **File:** `.github/workflows/pr-checks.yml` (L59)
- **Issue:** `python -m pytest tests/ -v ... || true` means test failures are ignored. Any security regression test, auth test, or validation test that fails will **not block the merge**. The TODO comment says "Remove || true once Cypher builds the test suite" — this is an active quality gap.
- **Fix:** Remove `|| true`. If tests are flaky, mark individual tests as `@pytest.mark.skip` rather than suppressing the entire suite.

### NEW-4. openpyxl ZIP Bomb / Decompression Attack Surface
- **Severity: MEDIUM**
- **OWASP:** A04 — Insecure Design
- **File:** `api/app/services/import_service.py` (L101, L297)
- **Issue:** `load_workbook(BytesIO(workbook_bytes), data_only=True)` processes uploaded files without decompression limits. XLSX files are ZIPs — a 10MB upload can decompress to gigabytes of XML, exhausting memory. openpyxl 3.1.5 has `defusedxml` detection but doesn't enforce it by default.
- **Fix:** Install `defusedxml` to activate openpyxl's built-in protection. Add a memory limit or process the workbook in a subprocess with resource limits.

### NEW-5. Cosmos DB Connection String Fallback Has No Monitoring
- **Severity: LOW**
- **OWASP:** A09 — Security Logging and Monitoring Failures
- **File:** `api/app/services/cosmos_client.py` (L17-23)
- **Issue:** When `key` is provided, `CosmosClient(endpoint, credential=key)` is used silently. No log differentiates whether the app connected via key or Managed Identity. If the CI accidentally leaves COSMOS_KEY set, production runs on a permanent credential with no alert.
- **Fix:** Log which auth method was used at startup. Alert on key-based auth in production.

---

## Remediation Priority (Switch's Top 15)

Reordered by **actual risk to this specific application** — a small NGO financial management tool behind Entra ID, deployed on Azure PaaS.

| Priority | ID | Finding | Severity | Effort | Why This Order |
|----------|----|---------|----------|--------|---------------|
| **1** | C5 | COSMOS_KEY in CI workflow | CRITICAL | Low | Permanent DB credential in a GitHub secret. If leaked, full data access. **Remove one line from deploy-prod.yml.** |
| **2** | C4 | Cosmos DB local auth + public network | CRITICAL | Medium | Even with RBAC, primary keys still work. Combined with no network restriction = anyone with the key has full access from anywhere. |
| **3** | H3→C | File upload: no magic bytes + ZIP bomb | CRITICAL | Low | Upload `application/octet-stream` → openpyxl processes blindly → resource exhaustion. Install `defusedxml`, add magic byte check. |
| **4** | C2 | CORS wildcards | CRITICAL | Low | 5-minute fix. Change `allow_methods` and `allow_headers` to explicit lists. |
| **5** | C3 | No CSP / security headers (frontend) | CRITICAL | Medium | Add `globalHeaders` to `staticwebapp.config.json`. Without this, M1 (token theft via XSS) is viable. |
| **6** | H1 | JWT error detail leakage | HIGH | Low | Replace one f-string with a generic message. 2-minute fix. |
| **7** | NEW-1 | python-jose unmaintained | HIGH | Medium | Migrate JWT validation to PyJWT (already installed). Removes unmaintained dependency entirely. |
| **8** | H7+H8 | Workflow permissions + SHA pinning | HIGH | Low | Add `permissions:` blocks. Pin actions to SHA. Low effort, high supply-chain impact. |
| **9** | H9 | OIDC migration | HIGH | Medium | Replace `AZURE_CREDENTIALS` with federated credential + `azure/login@v2` OIDC. |
| **10** | C1→H | Rate limiting | HIGH | Medium | Add `slowapi`. Prioritize `/api/imports` and `/api/export` which are resource-intensive. |
| **11** | H2 | Security headers (API) | HIGH | Low | Add security headers middleware to FastAPI. |
| **12** | H5+H6 | Key Vault purge + SWA config | HIGH | Low | Two one-line Bicep changes. |
| **13** | NEW-2 | Swagger exposed in prod | MEDIUM | Low | Conditional `docs_url=None` in production. |
| **14** | NEW-3 | PR tests swallowed | MEDIUM | Low | Remove `|| true` from pr-checks.yml. |
| **15** | C6→H | App Insights public access | HIGH | Low | Set both to `'Disabled'` in Bicep. |

### Quick Wins (< 15 minutes each)
- C2 (CORS): explicit method/header lists
- C5: remove COSMOS_KEY line from deploy-prod.yml
- H1: generic error message
- H5: `enablePurgeProtection: true`
- H6: `allowConfigFileUpdates: false`
- NEW-2: conditional Swagger disable
- NEW-3: remove `|| true`

### Remaining items (Next Sprint)
- M1 (sessionStorage), M4 (date range validation), M5 (Decimal math), M7 (retention), M8 (diagnostics), L1-L5, NEW-5

---

## Notes for Pedro

1. **The team did genuinely good work.** 28 findings from generalists with correct OWASP mapping is solid. I mostly agreed with their assessments — just adjusted 4 severities and added 5 they missed.

2. **The #1 priority is the COSMOS_KEY in CI** — the Bicep correctly uses Key Vault references, but the deploy workflow overrides them with a plaintext secret. This is the highest-impact fix you can make in 5 minutes.

3. **python-jose needs to go.** It's unmaintained and you already have PyJWT installed via MSAL. This is a dependency consolidation win, not just a security fix.

4. **The `|| true` on tests is a ticking time bomb.** If you're not running tests, you're not catching regressions. Either fix the test suite or accept the risk explicitly.

5. **C3 and M1 are linked.** Without CSP, XSS can steal localStorage tokens. Fix both together — CSP headers + move to sessionStorage.
