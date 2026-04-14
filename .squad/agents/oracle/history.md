# Oracle — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->
- **2026-04-14 — Product renamed:** "NGO Treasury" → "OpenTreasury" for the public repo. Renamed across all docs, specs, security reports, manifest.json, and SCSS comments. Azure resource names (rg-ngo-treasury-*, cosmos-ngo-treasury-*, etc.) and the `ngo-treasury` database name are intentionally kept — those are live infra identifiers. Generic "NGO" references (the category of organizations served) are also preserved. Remaining "NGO Treasury" in code files (main.py, app.component.ts, index.html, Bicep modules, setup/teardown scripts) are outside docs scope — flagged for other agents.
- **2026-04-14 — Docs fully genericized:** No org-specific references remain in docs. azure-setup.md resource names updated from `ngo-treasury` to `opentreasury` (40 occurrences). README.md env var examples updated. phase-1-frontend-ux-spec.md "Rett Spain" reference genericized. Security docs and CONTRIBUTING.md were already clean. Note: `docs/architecture.md` still has `ngo-treasury` naming convention examples — flag for next pass if needed.
