# Orchestration Log — Oracle (📝 Docs)

**Session:** naming-rename  
**Date:** 2026-04-14  
**Mode:** background  

## Task

Rename product name from "NGO Treasury" to "OpenTreasury" across documentation and metadata files.

## Files Modified (13)

- CONTRIBUTING.md
- README.md
- frontend/README.md
- infra/README.md
- docs/features.md
- docs/architecture.md
- docs/guides/azure-setup.md
- docs/security/README.md
- docs/security/scan-2026-04-12.md
- docs/specs/functional-requirements-gap-analysis.md
- frontend/public/manifest.json
- frontend/src/_tokens.scss
- frontend/jest.config.ts

## Scope Rules

- **Renamed:** "NGO Treasury" → "OpenTreasury" in titles, descriptions, manifest, SCSS comments.
- **Preserved:** Azure resource names (`rg-ngo-treasury-*`, `cosmos-ngo-treasury-*`, etc.), database name, generic "NGO" category references.

## Decision Inbox

- `oracle-naming-rename.md` — documents what was renamed, what was preserved, and remaining work for other agents.

## Result

✅ Completed. No errors.
