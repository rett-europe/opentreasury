# Niobe — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Deploy template spec — adopter experience review
- Reviewed Neo's deploy-template-spec.md from an adopter UX perspective. The spec is technically solid (2-file template, DRY architecture) but written by engineers for engineers.
- Defined the realistic adopter persona: "Ana" — NGO IT contact, Windows user, can follow instructions but doesn't know Bicep/GitHub Actions/service principals.
- Mapped the full adopter lifecycle: Discovery → Evaluation → Prerequisites → Provisioning → First Deploy → First Use → Operations. The spec only covers Provisioning + First Deploy.
- **Critical gap:** Post-deployment onboarding is completely missing — no guidance on Entra role assignment, first account/category setup, or first import.
- **Critical gap:** Script output names don't 1:1 match GitHub secret names — high confusion risk for adopters.
- **Critical gap:** Windows/PowerShell path not mentioned in spec despite `setup-azure.ps1` existing.
- **30-minute claim is unrealistic.** Mapped actual steps: optimistic = 28 min, realistic = 82 min. Recommended changing to "about an hour" with qualifier.
- Versioning UX has significant gaps: no notification mechanism, `product_ref` is git-speak, default to `main` means deploying unreleased code, no rollback documentation.
- Key files: `docs/specs/deploy-template-spec.md`, `scripts/setup-azure.sh`, `scripts/setup-azure.ps1`, `docs/guides/azure-setup.md`
- **Lesson:** Technical specs need persona-first thinking. The adopter lifecycle extends far beyond "deploy completes." Post-deployment onboarding, versioning, and error recovery are where adoption succeeds or fails.
- Asked to be involved in writing the deploy template README.

### 2026-04-14: Deploy template README — adoption guide written
- Created `deploy-template/README.md` — full end-to-end adoption guide for NGO admins.
- Persona-first writing: "Ana" (most technical person at a 20-person NGO) is the target reader. No developer jargon.
- Structure: 18 sections covering the complete adopter lifecycle — discovery through teardown.
- Incorporated all review recommendations: outcomes-first intro, realistic "about an hour" estimate, cost table upfront, Windows/PowerShell parity, post-deployment onboarding (Entra role assignment, first account, first import), error recovery ("safe to re-run"), health-check verification checklist, symptom→check→fix troubleshooting for all known gotchas.
- Key design decisions: both bash and PowerShell commands shown for every CLI step; Azure Portal navigation spelled out step-by-step (e.g., "Enterprise Applications, not App registrations"); cost monitoring and budget alerts section added.
- **Note for Tank/Oracle:** The script output format (Step 9) in both `setup-azure.sh` and `setup-azure.ps1` still prints the legacy `AZURE_CREDENTIALS` secret and doesn't match the OIDC-based 1-secret + 8-variable classification from the spec. The scripts need updating to match the README's guidance. Filed as a decision.
- Key files: `deploy-template/README.md`, `docs/specs/deploy-template-spec.md`
