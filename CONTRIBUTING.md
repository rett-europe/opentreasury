# Contributing to OpenTreasury

Thank you for your interest in contributing to the OpenTreasury project.

## Development Setup

See the [README](README.md) for prerequisites and quick start instructions.

### Frontend

```bash
cd frontend
npm install
npx ng serve          # Dev server with mock data at http://localhost:4200
npx ng build          # Production build
npx ng test           # Run tests
npx ng lint           # Lint check
```

### Backend

```bash
cd api
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env                            # Configure Azure credentials
uvicorn app.main:app --reload --port 8000       # Dev server
python -m pytest                                # Run tests
black app/ tests/                               # Format code
flake8 app/ tests/                              # Lint check
```

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production. Auto-deploys on merge. |
| `feature/*` | New features. Branch from `main`, PR back to `main`. |
| `fix/*` | Bug fixes. Branch from `main`, PR back to `main`. |

## Pull Request Process

1. Create a feature or fix branch from `main`
2. Make your changes
3. Ensure both frontend and backend build without errors
4. Run tests (`npx ng test` and `python -m pytest`)
5. Open a PR against `main`
6. Request review

## Code Style

### Frontend
- **Angular 19+** standalone components (no NgModules)
- **TypeScript** strict mode
- **SCSS** for styles, Angular Material for UI
- **Spanish labels** in templates (MVP). English planned via i18n.
- Component names: `feature-name.component.ts`
- Service names: `feature-name.service.ts`

### Backend
- **Python 3.11+** with type hints
- **Black** for formatting (line length 120)
- **Flake8** for linting (line length 120)
- **Pydantic** for request/response validation
- Amounts use `Decimal` (never `float`) for financial precision
- All API endpoints require authentication
- All writes must create an audit log entry

## Project Conventions

### Data Model
- Transaction amounts are **signed**, with a `transactionType` field (`income`, `expense`, `transfer`, `refund`) that determines the sign.
- Categories have a `categoryType` (`income` or `expense`) for structural classification.
- Subcategories are **embedded** inside category documents.
- Tags and bank accounts share the `reference_data` Cosmos DB container.
- Soft deletes only — financial data is never permanently deleted.

### API
- REST endpoints under `/api/`
- camelCase in JSON responses (Pydantic alias generator)
- Cosmos DB queries use parameterized queries (never string formatting)
- Pagination via continuation tokens (not page numbers)
- Delete endpoints check for referencing transactions before allowing deletion

### Authentication
- Microsoft Entra ID (Azure AD) with your organization's tenant
- JWT Bearer tokens validated on every request
- RBAC: `Admin` app role = full access, no role = `Viewer` (read-only)

## Environment Flags

| Flag | Where | Purpose |
|------|-------|---------|
| `useMocks: true` | `frontend/src/environments/environment.ts` | Run frontend with mock data (default — no backend needed) |
| `useMocks: false` | `frontend/src/environments/environment.prod.ts` | Production — real API calls |

## Getting Help

Open an issue in the repository or reach out to the team.
