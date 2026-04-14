# Orchestration Log — Morpheus (🔧 Backend)

**Session:** naming-rename  
**Date:** 2026-04-14  
**Mode:** foreground  

## Task

Rename "ngo-treasury" → "opentreasury" in backend code and config.

## Files Modified

- api/app/config.py (COSMOS_DATABASE_NAME default)
- api/app/middleware/error_handler.py (logger name)
- api/.env.example
- api/.env.cosmos-emulator.example

## Verification

- `flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__` — ✅ pass
- `black --check app/ tests/ --line-length=120` — ✅ pass
- `pytest tests/ -v` — 324 pass / 9 fail (pre-existing fixture issues, unrelated to rename)

## Decision Inbox

- `morpheus-db-name-rename.md` — documents impact on existing deployments (must set `COSMOS_DATABASE_NAME=ngo-treasury` or recreate DB).

## Result

✅ Completed. Lint + format clean. Test failures are pre-existing.
