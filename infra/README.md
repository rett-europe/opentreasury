# OpenTreasury — Azure Infrastructure

Bicep templates to provision all Azure resources for the OpenTreasury application.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) v2.50+
- An Azure subscription
- A resource group already created (e.g., `rg-opentreasury-dev`)
- An Entra ID app registration for the API (you need the tenant ID and client ID)

## Resources Provisioned

| Resource | SKU | Purpose |
|----------|-----|---------|
| Cosmos DB (NoSQL) | Serverless | Database — transactions, categories, reference_data, audit_log |
| App Service Plan | B1 (Linux) | Hosting plan for the API |
| App Service | Python 3.12 | FastAPI backend with Managed Identity |
| Static Web App | Free | Angular frontend |
| Key Vault | Standard | Secrets — Cosmos endpoint, Entra ID config |
| Application Insights | Pay-as-you-go | Monitoring & diagnostics |
| Log Analytics Workspace | PerGB2018 | Backing store for App Insights |

## Deployment

### Dev environment

```bash
az deployment group create \
  --resource-group rg-opentreasury-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam \
  --parameters azureTenantId='<YOUR_TENANT_ID>' azureClientId='<YOUR_CLIENT_ID>'
```

### Production environment

```bash
az deployment group create \
  --resource-group rg-opentreasury-prod \
  --template-file infra/main.bicep \
  --parameters infra/parameters/prod.bicepparam \
  --parameters azureTenantId='<YOUR_TENANT_ID>' azureClientId='<YOUR_CLIENT_ID>'
```

> `azureTenantId` and `azureClientId` are `@secure()` parameters — pass them at deploy time or via a Key Vault parameter file. Never commit them to source control.

## Architecture

```
Static Web App (Angular) → App Service (FastAPI, Python 3.12)
                                  │
                                  ├─→ Cosmos DB (Serverless, RBAC via Managed Identity)
                                  ├─→ Key Vault (secrets via Managed Identity)
                                  └─→ Application Insights (telemetry)
```

## Resource Naming

| Type | Pattern | Example |
|------|---------|---------|
| Cosmos DB | `cosmos-{project}-{env}` | `cosmos-opentreasury-prod` |
| App Service Plan | `plan-{project}-{env}` | `plan-opentreasury-prod` |
| App Service | `app-{project}-{env}` | `app-opentreasury-prod` |
| Static Web App | `swa-{project}-{env}` | `swa-opentreasury-prod` |
| Key Vault | `kv{project}{env}` | `kvopentreasuryprod` |
| App Insights | `ai-{project}-{env}` | `ai-opentreasury-prod` |
| Log Analytics | `log-{project}-{env}` | `log-opentreasury-prod` |

## Security

- **No connection strings** — Cosmos DB data access uses RBAC (Managed Identity)
- **Key Vault references** — App Service reads secrets via `@Microsoft.KeyVault(...)` references
- **RBAC assignments** — App Service's Managed Identity gets:
  - `Cosmos DB Built-in Data Contributor` on the Cosmos account (data plane)
  - `Key Vault Secrets User` on the Key Vault
- **HTTPS only** — enforced on App Service
- **TLS 1.2 minimum** — enforced on App Service
- **FTPS disabled** — no FTP access to App Service
