# System Settings — Security Review (Issue #12)

**Reviewer:** Switch (Security Engineer)
**Date:** 2026-04-18
**Branch:** `feature/system-settings-issue-12`
**Scope:** Admin-only `PUT /api/settings`, amendment A1 (`updatedBy`/`updatedAt` source of truth), post-refactor auth layer status (commit `cab41d5`).
**Status:** Approved for implementation — all MUSTs in §6 must be met before merge.

---

## 1. Verdict

**YES — the spec's admin-only assumptions (§10, US-6) remain valid after `cab41d5`.**

The auth refactor removed dev-mode mocks but preserved production role enforcement. `get_current_admin()` is correctly wired in all admin-only routers. No regression detected. The frontend `adminGuard` exists. **Backend enforcement does not depend on frontend gating.**

---

## 2. Backend Admin Enforcement — Current State

### 2.1 How "admin" is determined

| Layer | Method | Source | Precedence |
|-------|--------|--------|-----------|
| JWT | `roles` claim | Entra ID token (MSAL) | Primary — only source of truth |
| Backend | `_resolve_role()` in `app/auth/dependencies.py` | `"Admin" in payload["roles"]` → `"Admin"`, else `"Viewer"` | Deterministic, no exceptions |
| Frontend | `AuthService.isAdmin()` signal | `GET /api/me` (role derived server-side from JWT) | Read-only post-login |

### 2.2 Backend dependency for the PUT handler

**Use this — already used by categories, imports, tags, accounts:**

```python
async def update_settings(
    data: SystemSettingsUpdate,
    current_user: dict = Depends(get_current_admin),
    service: SystemSettingsService = Depends(get_system_settings_service),
) -> SystemSettingsResponse:
    ...
```

**Why most secure:** chains token validation → role extraction → role assertion in one declarative dependency. Fail-closed: if `get_current_admin` raises, the handler never runs. No scattered `if user["role"] == "Admin"` checks to forget in code review.

### 2.3 Anti-patterns to refuse

| Option | Why no |
|--------|--------|
| Manual role check in handler | Easy to forget; harder to audit |
| Role decorator | Mixes security with business logic; less discoverable |
| Frontend-only check | Trivially bypassed by anyone with a network proxy |

---

## 3. Frontend Admin Enforcement — Current State

### 3.1 Route gating

```typescript
{
  path: 'settings',
  loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
  canActivate: [MsalGuard, adminGuard],
}
```

`adminGuard` (in `frontend/src/app/core/auth/`) checks `authService.isAuthenticated()` then `authService.isAdmin()`. Viewers are silently redirected to `/dashboard`.

### 3.2 Sidenav visibility

Wrap the Settings nav entry in `@if (authService.isAdmin())` — viewers never see the link.

### 3.3 Defense in depth — confirmed

The backend `PUT /api/settings` MUST use `Depends(get_current_admin)` regardless of frontend behaviour. A captured viewer token or a manipulated frontend will be rejected with 403 at the API boundary. **The backend never trusts the frontend.**

---

## 4. A1 — `updatedBy` Source of Truth

### 4.1 Where the principal is exposed

| Layer | Source | Available |
|-------|--------|-----------|
| FastAPI security | `HTTPBearer` + JWT validation | Raw payload |
| `get_current_user` | `app/auth/dependencies.py` | `{"oid", "name", "email", "roles", "role"}` |
| Router handler | `Depends(get_current_admin)` | Same dict |
| Service | Handler-passed parameters | `oid`, optionally `name` |

### 4.2 Identifier to store

**Use `oid` (Entra object ID) as `updatedBy`.** Optionally store a readable secondary `updatedByName`.

| Identifier | Stable? | Auditable? | Verdict |
|-----------|---------|-----------|---------|
| `oid` | ✅ Immutable across name/email/password changes | Unambiguous | **USE** |
| `preferred_username` | ⚠️ Reassignable | Readable | Not as primary |
| `name` | ❌ Changes anytime | Readable | Secondary only |
| `email` | ⚠️ Changes | Readable | Secondary only |

### 4.3 Implementation

```python
async def update_settings(
    data: SystemSettingsUpdate,
    current_user: dict = Depends(get_current_admin),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    return await service.update_settings(
        data=data,
        updated_by_oid=current_user["oid"],
        updated_by_name=current_user.get("name", ""),
        updated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
```

### 4.4 Confirm no client-supplied path

```python
class SystemSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unknown fields
    currency: CurrencyCode
    dateFormat: DateFormat
    numberFormat: NumberFormat
    fiscalYearStartMonth: int = Field(ge=1, le=12)
    defaultLanguage: Literal["es", "en"]
    organizationName: str = Field(default="", max_length=80)
    # NO updatedBy, NO updatedAt
```

`extra="forbid"` ensures any client attempt to set `updatedBy`/`updatedAt` returns 422. Server-side fields are stamped just before the Cosmos write.

---

## 5. Threat Model — System Settings Specific

| Threat | Impact | Mitigation (V1) | Status |
|--------|--------|-----------------|--------|
| Non-admin PUT (privilege escalation) | Currency/format flipped for everyone | `Depends(get_current_admin)` → 403 | ✅ Sufficient |
| Stolen admin token (phishing) | Settings tampered org-wide | Short JWT lifetime, MSAL refresh-token model, TLS | ✅ Recommend MFA at Entra org level |
| Cross-org tampering | N/A | OpenTreasury is single-tenant per deployment | ✅ Out of scope |
| Replay / stale write (concurrent admins) | Last write wins silently | Spec §11 accepts this for V1; A1 audit fields stamped | ⚠️ Document as known limitation; ETag in V1.1 |
| Unauthenticated GET | Disclosure of currency/date/org name | GET still requires `get_current_user`; viewers need this to render | ✅ Acceptable — not secrets |
| Stored XSS via org name | XSS in browser/exports | Pydantic max-length 80; Angular interpolation `{{ }}` escapes by default | ✅ Verify in code review no `[innerHTML]` binding |
| Org name DOS (storage bloat) | Cosmos bloat, broken filenames | `Field(max_length=80)` + `.strip()` | ✅ Sufficient |
| Settings load failure | App boot stall | Fall back to hard-coded defaults; log warning; banner on Settings page | ✅ Acceptable |
| Rapid-fire PUT (DOS, RU burn) | Quota exhaustion | None in code today; enforce at SWA / App Gateway | ⚠️ Out of V1 scope; track for follow-up |

---

## 6. Required Hardening for V1 (MUSTs)

Each is testable. Morpheus + Trinity must implement all.

1. **Backend rejects invalid `currency`.** Whitelist `["EUR", "USD", "GBP", "CHF"]`. Invalid → 422. *Test:* `test_put_settings_invalid_currency_returns_422`.
2. **`updatedBy` always from JWT `oid`, never client.** Pydantic `extra="forbid"`; service overrides if present. *Test:* `test_put_settings_client_supplied_updatedby_rejected`.
3. **`updatedAt` always server clock (UTC ISO 8601), never client.** *Test:* `test_put_settings_updated_at_within_one_second_of_server_time`.
4. **Non-admin PUT → 403 from backend.** *Test:* `test_put_settings_viewer_role_returns_403`.
5. **GET accessible to any authenticated user (not admin-only).** *Test:* `test_get_settings_viewer_can_read`.
6. **`organizationName` trimmed and limited to 80 chars.** *Test:* `test_put_settings_organization_name_trimmed_and_truncated`.
7. **All enum fields reject out-of-range values.** *Tests:* `test_put_settings_invalid_date_format_returns_422`, etc.
8. **Frontend hides Settings menu and route from viewers.** *Tests:* `test_settings_menu_hidden_for_viewer_role`, `test_settings_route_redirects_viewer_to_dashboard`.
9. **Code/comments explain why GET is not admin-only.** Prevent future maintainers tightening it accidentally.
10. **Cosmos document stored at `id="system"`, `type="system_settings"`** in the chosen container (defer container choice to Morpheus's scoping). *Test:* repository round-trip test.

---

## 7. Recommended Hardening (Post-V1)

- Optimistic concurrency via ETag (close A1's deferred door).
- Rate limiting on PUT (App Gateway / SWA layer or FastAPI middleware).
- Separate audit log container (richer than `updatedAt`/`updatedBy`).
- MFA enforcement at Entra (org-level, outside this codebase).

---

## 8. Sign-off Conditions

Switch will approve the implementation PR when:

1. All 10 MUSTs from §6 are implemented and tested.
2. `pytest tests/ -v --override-ini="addopts="` passes; `npx ng test` passes (if extant).
3. Code review confirms:
   - PUT uses `Depends(get_current_admin)` (not manual checks).
   - `SystemSettingsUpdate` Pydantic model uses `extra="forbid"` and has no `updatedBy`/`updatedAt`.
   - `updatedBy` is `current_user["oid"]`; `updatedAt` is server-side `datetime.now(timezone.utc)`.
   - Cosmos doc stores both fields; response returns both.
   - `organizationName` is rendered via `{{ }}` interpolation only.
4. Lint clean: `flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__`, `black --check app/ tests/ --line-length=120`.
5. Frontend lint + build clean: `npx ng lint`, `npx ng build --configuration=production`.

---

## Appendix — Commit `cab41d5` Impact

**"refactor(auth): simplify security dependency and remove dev mode mock user logic"**

- Removed dev-mode auth bypass (mock user injection).
- Production auth dependencies unchanged.
- Admin role resolution unchanged.

**Verdict:** Security-positive. Reduces accidental production auth bypass. No new risks.
