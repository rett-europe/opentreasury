# OpenTreasury

Open-source treasury management application for NGOs. Helps administrative staff track bank transactions, income, and expenses with categories, subcategories, and tags for proper financial oversight.

Designed to be extensible — any non-profit organization can fork, configure, and deploy to their own Azure subscription.

## Architecture

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Angular 19+, Angular Material, MSAL Angular | Azure Static Web Apps (Free) |
| Backend | Python FastAPI, async Cosmos DB SDK | Azure App Service B1 |
| Database | Azure Cosmos DB NoSQL (Serverless) | ~€1-5/month |
| Auth | Microsoft Entra ID (your tenant) | Employees only |
| IaC | Bicep | GitHub Actions |

**Estimated monthly cost:** ~€20-25

```mermaid
graph TD
    Users["👤 Users"] -->|HTTPS| SWA
    SWA -->|"Bearer token"| API
    API -->|"async SDK"| Cosmos
    API -.->|secrets| KV
    API -.->|telemetry| AI

    SWA["Azure Static Web Apps<br/>Angular SPA + Entra ID Login<br/><i>Free tier</i>"]
    API["App Service B1<br/>Python FastAPI<br/>+ Managed Identity"]
    KV["Key Vault"]
    AI["App Insights"]

    subgraph CosmosDB["Cosmos DB NoSQL · Serverless"]
        T["transactions"]
        C["categories"]
        R["reference_data"]
        A["audit_log"]
    end
    Cosmos --- T
    Cosmos --- C
    Cosmos --- R
    Cosmos --- A
    Cosmos["Cosmos DB Account"]

    style Users fill:#f3e5f5,stroke:#ce93d8,color:#4a148c
    style SWA fill:#e8d5f5,stroke:#b39ddb,color:#4a148c
    style API fill:#d7c4e8,stroke:#9575cd,color:#311b92
    style Cosmos fill:#c5e1a5,stroke:#aed581,color:#33691e
    style CosmosDB fill:#f1f8e9,stroke:#c5e1a5,color:#33691e
    style T fill:#fff9c4,stroke:#fff176,color:#f57f17
    style C fill:#fff9c4,stroke:#fff176,color:#f57f17
    style R fill:#fff9c4,stroke:#fff176,color:#f57f17
    style A fill:#fff9c4,stroke:#fff176,color:#f57f17
    style KV fill:#fce4ec,stroke:#f48fb1,color:#880e4f
    style AI fill:#e0f7fa,stroke:#80deea,color:#006064
```

## Project Structure

```
ngo-treasury/
├── frontend/          Angular 19 app (standalone components, MSAL auth)
├── api/               Python FastAPI backend
│   └── tests/         Backend test suite (pytest)
├── infra/             Bicep IaC (Cosmos DB, App Service, SWA, Key Vault, App Insights)
│   ├── modules/       Reusable Bicep modules
│   └── parameters/    Environment-specific parameter files (dev, prod)
├── docs/              Architecture docs, feature specs, security reviews
├── scripts/           Azure setup and teardown scripts
├── .github/workflows/ CI/CD pipelines + Squad automation
└── .squad/            AI team state (Squad coordination)
```

## Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **Angular CLI** (`npm install -g @angular/cli`)
- **Azure CLI** (for deployment)

## Quick Start

### Frontend (with mock data — no backend needed)

```bash
cd frontend
npm install
npx ng serve
```

Open http://localhost:4200 — logs in as a mock Admin user with 25 sample transactions.

> The frontend runs with mock data by default (`useMocks: true` in `environment.ts`). All API calls are intercepted and return realistic sample data. To connect to a real backend, see [Connecting Frontend to Backend](#connecting-frontend-to-backend).

### Backend

```bash
cd api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure credentials

uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/api/docs (Swagger UI, dev only — disabled in production).

### Connecting Frontend to Backend

In `frontend/src/environments/environment.ts`, set:

```typescript
useMocks: false,
apiBaseUrl: 'http://localhost:8000/api',
```

And configure the MSAL settings with your Entra ID app registration.

## Environment Variables (Backend)

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Entra ID tenant | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_ID` | Backend app registration client ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `COSMOS_ENDPOINT` | Cosmos DB account endpoint | `https://cosmos-ngo-treasury.documents.azure.com:443/` |
| `COSMOS_DATABASE_NAME` | Database name | `ngo-treasury` || `COSMOS_KEY` | Cosmos DB primary key (local dev only — Managed Identity in Azure) | `your-cosmos-key` || `CORS_ORIGINS` | Allowed frontend origins | `["http://localhost:4200"]` |

## Features

### MVP
- ✅ Transaction entry with categories, subcategories, and tags
- ✅ Multi-account support (4 bank accounts + PayPal)
- ✅ "Guardar y Nuevo" flow for fast daily data entry (~15s per transaction)
- ✅ Transaction search and filtering (account, date, category, tag, text)
- ✅ Category/subcategory management
- ✅ Tag management
- ✅ Bank account management
- ✅ Excel/CSV import from bank exports
- ✅ Excel export for accounting firm
- ✅ Dashboard with account balances and monthly summary
- ✅ Multi-language support (Spanish + English)
- ✅ RBAC: Admin (full access) / Viewer (read-only)
- ✅ Audit trail on all changes
- ✅ Soft deletes (financial data is never permanently lost)

### Planned
- Invoice file attachments
- PowerBI analytics integration
- Multi-currency support

## RBAC

| Role | Access |
|------|--------|
| **Admin** | Full read/write. Manages transactions, categories, tags, accounts. |
| **Viewer** | Read-only. Views transactions, reports, exports. Board members. |

Roles are assigned via Entra ID app roles.

## Cosmos DB Containers

| Container | Partition Key | Purpose |
|-----------|--------------|---------|
| `transactions` | `/partitionKey` ("YYYY-MM") | Financial transactions |
| `categories` | `/id` | Categories with embedded subcategories |
| `reference_data` | `/type` | Tags + bank accounts |
| `audit_log` | `/entityType` | Audit trail (7-year TTL) |

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR process.

## Documentation

- [Architecture overview](docs/architecture.md)
- [Feature catalog](docs/features.md)
- [Security reviews](docs/security/)
