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
