# Morpheus — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->
- (2026-04-14) Renamed "ngo-treasury" → "opentreasury" in backend identifiers: config default for COSMOS_DATABASE_NAME, logger name in error_handler, and both .env example files. The Entra ID audience claim (`api://ngo-treasury-api`) in conftest.py was intentionally left unchanged — it's tied to a live Azure app registration.
- (2026-04-14) Renamed AZURE_CLIENT_ID → ENTRA_API_CLIENT_ID across all backend Python code and .env files (6 occurrences in 5 files: config.py, auth/dependencies.py, conftest.py, .env.example, .env.cosmos-emulator.example). Per deploy-template-spec §4.5 — resolves collision with DefaultAzureCredential which auto-consumes AZURE_CLIENT_ID. Lint/format clean. 332 tests pass; 1 pre-existing failure in test_import_fixtures (unrelated to rename).
