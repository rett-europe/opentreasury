# Azure Setup Guide — NGO Treasury

Complete instructions for provisioning all Azure infrastructure, Entra ID app registrations, and GitHub Actions secrets.

---

## Table of Contents

- [1. Prerequisites](#1-prerequisites)
- [2. Automated Setup (Recommended)](#2-automated-setup-recommended)
- [3. Manual Setup (Step by Step)](#3-manual-setup-step-by-step)
  - [3.1 Create Resource Group](#31-create-resource-group)
  - [3.2 Entra ID: Backend API Registration](#32-entra-id-backend-api-registration)
  - [3.3 Entra ID: Frontend SPA Registration](#33-entra-id-frontend-spa-registration)
  - [3.4 Service Principal for GitHub Actions](#34-service-principal-for-github-actions)
  - [3.5 Deploy Infrastructure (Bicep)](#35-deploy-infrastructure-bicep)
  - [3.6 Configure GitHub Secrets](#36-configure-github-secrets)
  - [3.7 Update Frontend Config](#37-update-frontend-config)
  - [3.8 First Deploy](#38-first-deploy)
- [4. Teardown](#4-teardown)
- [5. Troubleshooting](#5-troubleshooting)

---

## 1. Prerequisites

Before you begin, make sure you have:

| Requirement | How to check |
|---|---|
| **Azure CLI** installed (2.50+) | `az --version` |
| **Logged in to Azure** | `az login` |
| **Correct subscription selected** | `az account show` — switch with `az account set --subscription <id>` |
| **Admin access** to your Entra ID tenant | Needed for app registrations and admin consent |
| **GitHub repo admin access** | Needed to set repository secrets |
| **Bicep CLI** (bundled with Azure CLI 2.20+) | `az bicep version` |

### Install Azure CLI

- **Windows:** `winget install Microsoft.AzureCLI`
- **macOS:** `brew install azure-cli`
- **Linux:** See [docs.microsoft.com/cli/azure/install-azure-cli](https://docs.microsoft.com/cli/azure/install-azure-cli)

---

## 2. Automated Setup (Recommended)

The fastest way to get everything running. The script creates all resources, app registrations, and prints the secrets you need.

### On Linux / macOS / WSL / Cloud Shell

```bash
chmod +x scripts/setup-azure.sh
./scripts/setup-azure.sh
```

### On Windows (PowerShell)

```powershell
.\scripts\setup-azure.ps1
```

### What the script creates

| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `rg-ngo-treasury-prod` | Container for all Azure resources |
| Cosmos DB (Serverless) | `cosmos-ngo-treasury-prod` | NoSQL database |
| App Service (Python 3.12) | `app-ngo-treasury-prod` | FastAPI backend |
| Static Web App | `swa-ngo-treasury-prod` | Angular frontend |
| Key Vault | `kvngotreasuryprod` | Secrets (Cosmos endpoint, tenant/client IDs) |
| Application Insights | `ai-ngo-treasury-prod` | Monitoring and logging |
| Log Analytics Workspace | `log-ngo-treasury-prod` | Log storage for App Insights |
| API App Registration | `ngo-treasury-api-prod` | Entra ID auth for backend API |
| SPA App Registration | `ngo-treasury-spa-prod` | Entra ID auth for Angular frontend |
| Service Principal | `sp-ngo-treasury-github-prod` | GitHub Actions deploy identity |

After the script finishes, it prints:
1. A table of GitHub secrets to set
2. The `AZURE_CREDENTIALS` JSON
3. Values for `environment.prod.ts`

---

## 3. Manual Setup (Step by Step)

If you prefer setting things up via the Azure Portal and CLI.

### 3.1 Create Resource Group

**Portal:**
1. Go to [portal.azure.com](https://portal.azure.com) → **Resource groups** → **Create**
2. Subscription: select yours
3. Resource group name: `rg-ngo-treasury-prod`
4. Region: **West Europe**
5. Tags: `project=ngo-treasury`, `environment=prod`
6. Click **Review + create** → **Create**

**CLI:**
```bash
az group create \
  --name rg-ngo-treasury-prod \
  --location westeurope \
  --tags project=ngo-treasury environment=prod
```

### 3.2 Entra ID: Backend API Registration

This app registration protects the FastAPI backend and defines the auth scopes and roles.

**Portal:**
1. Go to **Microsoft Entra ID** → **App registrations** → **New registration**
2. Name: `ngo-treasury-api-prod`
3. Supported account types: **Accounts in this organizational directory only** (single tenant)
4. Redirect URI: leave blank (API doesn't need one)
5. Click **Register**

**Configure the API:**

6. Go to **Expose an API**
7. Set the **Application ID URI** to: `api://ngo-treasury-api`
8. Click **Add a scope**:
   - Scope name: `access_as_user`
   - Who can consent: **Admins and users**
   - Admin consent display name: `Access NGO Treasury API`
   - Admin consent description: `Allow the application to access NGO Treasury API on behalf of the signed-in user`
   - State: **Enabled**
   - Click **Add scope**

**Configure App Roles:**

9. Go to **App roles** → **Create app role**
10. Create the **Admin** role:
    - Display name: `Admin`
    - Allowed member types: **Users/Groups**
    - Value: `Admin`
    - Description: `Admins can read and write all data`
    - Enable: checked
11. Create the **Viewer** role:
    - Display name: `Viewer`
    - Allowed member types: **Users/Groups**
    - Value: `Viewer`
    - Description: `Viewers can read data only (default for users without explicit role)`
    - Enable: checked

**Note the values:**
- **Application (client) ID** — this is `API_CLIENT_ID`
- **Object ID** — needed for updates

**CLI equivalent:**
```bash
# Create the app (app roles as JSON)
az ad app create \
  --display-name "ngo-treasury-api-prod" \
  --sign-in-audience "AzureADMyOrg" \
  --identifier-uris "api://ngo-treasury-api" \
  --app-roles '[
    {"allowedMemberTypes":["User"],"displayName":"Admin","isEnabled":true,"value":"Admin","description":"Admins can read and write all data"},
    {"allowedMemberTypes":["User"],"displayName":"Viewer","isEnabled":true,"value":"Viewer","description":"Viewers can read data only"}
  ]'

# Create the service principal
az ad sp create --id <API_CLIENT_ID>
```

### 3.3 Entra ID: Frontend SPA Registration

This app registration is used by the Angular frontend via MSAL.js.

**Portal:**
1. Go to **Microsoft Entra ID** → **App registrations** → **New registration**
2. Name: `ngo-treasury-spa-prod`
3. Supported account types: **Accounts in this organizational directory only**
4. Redirect URI:
   - Platform: **Single-page application (SPA)**
   - URI: `http://localhost:4200`
5. Click **Register**

> **Important:** Select **SPA** platform, NOT "Web". MSAL.js uses PKCE which requires the SPA platform.

**Add API permission:**

6. Go to **API permissions** → **Add a permission**
7. Select **My APIs** → `ngo-treasury-api-prod`
8. Select **Delegated permissions** → check `access_as_user`
9. Click **Add permissions**
10. Click **Grant admin consent for [your tenant]** (requires admin)

**Note the values:**
- **Application (client) ID** — this is `MSAL_CLIENT_ID` (used in Angular)

**CLI equivalent:**
```bash
# Create the SPA app
az ad app create \
  --display-name "ngo-treasury-spa-prod" \
  --sign-in-audience "AzureADMyOrg"

# Set SPA redirect URIs
az ad app update --id <SPA_OBJECT_ID> \
  --spa-redirect-uris "http://localhost:4200"

# Add API permission
az ad app permission add \
  --id <SPA_OBJECT_ID> \
  --api <API_CLIENT_ID> \
  --api-permissions "<SCOPE_ID>=Scope"

# Grant admin consent
az ad app permission admin-consent --id <SPA_OBJECT_ID>
```

### 3.4 Service Principal for GitHub Actions

Create a service principal scoped to the resource group, for CI/CD deployments.

```bash
az ad sp create-for-rbac \
  --name "sp-ngo-treasury-github-prod" \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/rg-ngo-treasury-prod \
  --sdk-auth
```

This outputs a JSON block — save it as the `AZURE_CREDENTIALS` GitHub secret.

### 3.5 Deploy Infrastructure (Bicep)

The Bicep templates in `infra/` define all Azure resources.

```bash
# Get your tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

# Deploy (prod)
az deployment group create \
  --resource-group rg-ngo-treasury-prod \
  --template-file infra/main.bicep \
  --parameters infra/parameters/prod.bicepparam \
  --parameters azureTenantId=$TENANT_ID azureClientId=<API_CLIENT_ID>
```

This creates: Cosmos DB, App Service, Static Web App, Key Vault, Application Insights, Log Analytics, and RBAC role assignments.

### 3.6 Configure GitHub Secrets

Go to **GitHub** → your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Add each of these:

| Secret Name | Value | Description |
|---|---|---|
| `AZURE_CREDENTIALS` | Service principal JSON from Step 3.4 | Full JSON block, not just the password |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID | GUID from `az account show` |
| `AZURE_RESOURCE_GROUP` | `rg-ngo-treasury-prod` | Resource group name |
| `AZURE_WEBAPP_NAME` | `app-ngo-treasury-prod` | App Service name for API deployment |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | SWA deployment token | Get with: `az staticwebapp secrets list --name swa-ngo-treasury-prod --resource-group rg-ngo-treasury-prod --query "properties.apiKey" -o tsv` |
| `MSAL_CLIENT_ID` | SPA app client ID | From Step 3.3 |
| `API_CLIENT_ID` | API app client ID | From Step 3.2 |

### 3.7 Update Frontend Config

Edit `frontend/src/environments/environment.prod.ts` with the real values:

```typescript
export const environment = {
  production: true,
  useMocks: false,
  apiBaseUrl: 'https://app-ngo-treasury-prod.azurewebsites.net/api',
  msal: {
    clientId: '<SPA_CLIENT_ID>',           // from Step 3.3
    tenantId: '<TENANT_ID>',               // from az account show
    authority: 'https://login.microsoftonline.com/<TENANT_ID>',
    redirectUri: 'https://<SWA_HOSTNAME>', // from az staticwebapp show
    postLogoutRedirectUri: 'https://<SWA_HOSTNAME>',
    apiScope: 'api://ngo-treasury-api/access_as_user',
  },
};
```

Also update the SPA app registration with the production redirect URI:
```bash
az ad app update --id <SPA_OBJECT_ID> \
  --spa-redirect-uris "http://localhost:4200" "https://<SWA_HOSTNAME>"
```

### 3.8 First Deploy

Push to `main` or merge a pull request. The GitHub Actions workflows will:

1. **Frontend:** Build Angular app → deploy to Static Web App
2. **Backend:** Package FastAPI app → deploy to App Service

```bash
git add .
git commit -m "feat: configure production environment"
git push origin main
```

---

## 4. Teardown

To delete all Azure resources and Entra ID registrations:

### On Linux / macOS / WSL / Cloud Shell

```bash
chmod +x scripts/teardown-azure.sh
./scripts/teardown-azure.sh
```

### On Windows (PowerShell)

```powershell
.\scripts\teardown-azure.ps1
```

The script will:
1. Ask you to type `DELETE` to confirm
2. Delete the resource group (all infra resources)
3. Delete both Entra ID app registrations
4. Delete the GitHub Actions service principal

**After teardown:**
- Remove all GitHub secrets from the repo settings
- Key Vault uses soft-delete — to purge immediately: `az keyvault purge --name kvngotreasuryprod`

---

## 5. Troubleshooting

### Wrong subscription

```
ERROR: The subscription '<id>' could not be found.
```

Fix: Run `az account list -o table` to list subscriptions, then `az account set --subscription <id>`.

### Missing permissions for app registrations

```
ERROR: Insufficient privileges to complete the operation.
```

Fix: You need **Application Administrator** or **Global Administrator** role in Entra ID. Ask your tenant admin.

### Admin consent failed

```
ERROR: Unable to grant admin consent.
```

Fix: Admin consent requires the **Global Administrator** or **Privileged Role Administrator** role. Grant consent manually in the Azure Portal: Entra ID → App registrations → `ngo-treasury-spa-prod` → API permissions → **Grant admin consent**.

### Key Vault soft-delete conflict

```
ERROR: A vault or HSM with the name 'kvngotreasuryprod' already exists in a deleted state.
```

Fix: Key Vault has a 90-day soft-delete retention. Either:
- Recover it: `az keyvault recover --name kvngotreasuryprod`
- Purge it: `az keyvault purge --name kvngotreasuryprod`

### Static Web App token not found

```
Could not retrieve SWA token
```

Fix: The SWA hasn't been deployed yet. Run the Bicep deployment first (Step 3.5), then re-run the setup script or get the token manually:
```bash
az staticwebapp secrets list \
  --name swa-ngo-treasury-prod \
  --resource-group rg-ngo-treasury-prod \
  --query "properties.apiKey" -o tsv
```

### Bicep deployment fails with "azureTenantId" or "azureClientId" error

These are secure parameters required by `infra/main.bicep` that aren't in the `.bicepparam` file.
Pass them explicitly:

```bash
az deployment group create \
  --resource-group rg-ngo-treasury-prod \
  --template-file infra/main.bicep \
  --parameters infra/parameters/prod.bicepparam \
  --parameters azureTenantId=<TENANT_ID> azureClientId=<API_CLIENT_ID>
```

### CORS errors in the browser

The backend CORS is configured to allow the SWA URL. If you see CORS errors:
1. Check that the SWA URL in `app-service.bicep` matches the actual SWA hostname
2. Verify the Bicep deployment completed successfully
3. Restart the App Service: `az webapp restart --name app-ngo-treasury-prod --resource-group rg-ngo-treasury-prod`

### MSAL "redirect_uri mismatch" error

The redirect URI in the SPA app registration must exactly match the URL in `environment.prod.ts`. Check:
1. App registration → Authentication → SPA redirect URIs
2. Ensure `http://localhost:4200` (dev) and `https://<swa-hostname>` (prod) are both listed
3. Make sure the platform is **SPA**, not **Web**
