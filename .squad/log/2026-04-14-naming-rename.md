# Session Log — 2026-04-14 — Naming Rename

**Goal:** Rename product from "NGO Treasury" / "ngo-treasury" to "OpenTreasury" / "opentreasury" across the codebase.

## Agents

| Agent | Scope | Result |
|-------|-------|--------|
| Oracle (📝 Docs) | 13 doc/metadata files | ✅ Clean |
| Trinity (⚛️ Frontend) | package.json, angular.json, localStorage keys, README | ✅ Lint + build pass |
| Morpheus (🔧 Backend) | config.py, error_handler.py, .env examples | ✅ Lint + format pass; 9 pre-existing test failures |

## Decisions Captured

1. **Product renamed** — "NGO Treasury" → "OpenTreasury" in all user-facing text. Azure resource names and DB name preserved.
2. **Cosmos DB default changed** — `COSMOS_DATABASE_NAME` default is now `opentreasury`. Existing deployments need env override or DB rename.

## Remaining Work

- Code files outside docs/frontend/backend scope still reference "NGO Treasury" (infra comments, scripts, conftest docstring). See `oracle-naming-rename.md` for full list.
