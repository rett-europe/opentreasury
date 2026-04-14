# OpenTreasury — Deployment Guide

> **Your organization's finances, under your control.**
>
> OpenTreasury is an open-source tool that helps non-profit organizations manage bank transactions, categorize spending, and produce financial reports. It runs in your own Azure subscription, so your financial data stays yours. This guide walks you through deploying it — no programming required.

---

## What you'll need

Before you start, make sure you have the following. The entire setup takes **about an hour** for someone doing it for the first time.

| Prerequisite | What it means | How to check |
|---|---|---|
| **Azure subscription** | A pay-as-you-go Azure account. Free trial or Visual Studio subscriptions also work. | Go to [portal.azure.com](https://portal.azure.com) and sign in. If you see a dashboard, you have one. |
| **Entra ID admin access** | Permission to create app registrations in your organization's Microsoft Entra ID (formerly Azure Active Directory). | Ask your IT admin: "Can I create app registrations in our Azure AD?" |
| **GitHub account** | A free GitHub account to host your deployment repository. | Go to [github.com](https://github.com) and sign in. |
| **Azure CLI** | A command-line tool for managing Azure resources. | See [How to install the Azure CLI](#how-to-install-the-azure-cli) below. |
| **Git** | Version control tool to download the project files. | Open a terminal and run `git --version`. If it prints a version number, you're set. |

> **No programming required.** You don't need to know Python, JavaScript, or any programming language. You'll edit a few configuration values and run a script — that's it.

### How to install the Azure CLI

**Windows (PowerShell):**
```powershell
winget install Microsoft.AzureCLI
```

**macOS:**
```bash
brew install azure-cli
```

**Linux (Ubuntu/Debian):**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

After installing, verify it works:

```
az --version
```

You should see a version number (2.x or later).

### Optional: GitHub CLI

The `gh` command-line tool makes creating repositories easier, but it's optional — you can also create repos through the GitHub website.

**Windows (PowerShell):**
```powershell
winget install GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
sudo apt install gh
```

---

## Estimated cost

OpenTreasury is designed to be affordable for small organizations. Here's what it costs to run:

| Resource | What it does | Monthly cost (estimate) |
|---|---|---|
| App Service (B1) | Runs the backend API | ~€12 |
| Cosmos DB (Serverless) | Stores your transaction data | ~€1–5 (depends on usage) |
| Static Web App (Free) | Hosts the web interface | €0 |
| Key Vault | Stores configuration secrets securely | < €1 |
| Application Insights | Monitors application health | < €1 |
| **Total** | | **~€15–25/month** |

These costs depend on your Azure region and usage. A 20-person NGO with a few hundred transactions per month will typically be at the lower end.

> **Tip:** You can reduce costs further by enabling Cosmos DB Free Tier (one free account per Azure subscription — ask your IT admin if it's already in use).

---

## Step 1: Create your deployment repository

Your deployment repository is a private GitHub repo that holds your organization's deployment configuration. It's separate from the OpenTreasury product code, so your configuration stays private.

**Option A: Using GitHub CLI**

```bash
gh repo create your-org/opentreasury-deploy --private --clone
cd opentreasury-deploy
```

**Option B: Using the GitHub website**

1. Go to [github.com/new](https://github.com/new)
2. Name it `opentreasury-deploy` (or whatever you prefer)
3. Set it to **Private**
4. Click **Create repository**
5. Clone it to your computer:
   ```bash
   git clone https://github.com/your-org/opentreasury-deploy.git
   cd opentreasury-deploy
   ```

> **Replace `your-org`** with your actual GitHub organization or username throughout this guide.

---

## Step 2: Clone the product repository

Download the OpenTreasury product code. You'll need it to run the setup script.

```bash
git clone https://github.com/rett-europe/opentreasury.git
cd opentreasury
```

---

## Step 3: Configure setup variables

Open the setup script and edit the clearly-labeled variables at the top. There are only 5 values to change.

**On Windows,** open `scripts\setup-azure.ps1` in any text editor (Notepad works fine).

**On macOS/Linux,** open `scripts/setup-azure.sh` in any text editor.

Edit these variables:

| Variable | What to put | Example |
|---|---|---|
| `PROJECT_NAME` | A short name for your deployment. Use lowercase letters only, no spaces. | `opentreasury` |
| `ENVIRONMENT` | `prod` for your live system, `dev` for testing | `prod` |
| `LOCATION` | The Azure region closest to your organization. See [Azure regions](https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies/). | `westeurope` |
| `TENANT_DOMAIN` | Your organization's Entra ID domain. Find it in Azure Portal → Microsoft Entra ID → Overview → Primary domain. | `myorg.onmicrosoft.com` |
| `GITHUB_REPO` | Your deploy repo from Step 1, in `owner/repo` format. | `your-org/opentreasury-deploy` |

**Example (bash):**
```bash
PROJECT_NAME="opentreasury"
ENVIRONMENT="prod"
LOCATION="westeurope"
TENANT_DOMAIN="myorg.onmicrosoft.com"
GITHUB_REPO="my-ngo/opentreasury-deploy"
```

**Example (PowerShell):**
```powershell
$ProjectName     = "opentreasury"
$Environment     = "prod"
$Location        = "westeurope"
$TenantDomain    = "myorg.onmicrosoft.com"
$GitHubRepo      = "my-ngo/opentreasury-deploy"
```

> **Leave the other variables alone.** The "derived names" section below will calculate the rest automatically.

---

## Step 4: Provision Azure resources

This step creates everything you need in Azure: a resource group, database, web hosting, identity configuration, and more. It takes about **10–15 minutes** to run.

### Log in to Azure

```bash
az login
```

This opens your browser. Sign in with an account that has admin access to your organization's Entra ID.

### Run the setup script

**On macOS/Linux (bash):**
```bash
chmod +x scripts/setup-azure.sh
./scripts/setup-azure.sh
```

**On Windows (PowerShell):**
```powershell
.\scripts\setup-azure.ps1
```

The script will:
1. Ask you to confirm your Azure subscription
2. Create a resource group with all infrastructure (database, web app, key vault, etc.)
3. Create identity configurations for login (Entra ID app registrations)
4. Create a service principal (a machine account) for automated deployments
5. Print a table of values you'll need in the next step

> **The script is safe to re-run.** If something goes wrong halfway through, or if you need to change a setting, just run it again. It detects what already exists and skips those steps — it won't create duplicates.

### Save the output

When the script finishes, it prints a table of GitHub configuration values. **Keep this terminal open** — you'll need these values in the next step.

The output looks like this:

```
▶ GitHub Secrets Summary

  Set these in: https://github.com/your-org/opentreasury-deploy/settings/secrets/actions

  ╔════════════════════════════════════════╦═══════════════════════╗
  ║ Name                                   ║ Value                 ║
  ╠════════════════════════════════════════╬═══════════════════════╣
  ║ AZURE_CREDENTIALS                      ║ <JSON blob>           ║
  ║ AZURE_SUBSCRIPTION_ID                  ║ xxxxxxxx-xxxx-...     ║
  ║ ...                                    ║ ...                   ║
  ╚════════════════════════════════════════╩═══════════════════════╝
```

---

## Step 5: Set GitHub configuration

The deployment workflows need to know your Azure configuration. You'll set **1 Secret** (sensitive) and **8 Variables** (non-sensitive) in your deploy repo's GitHub settings.

### Navigate to GitHub Settings

1. Go to your deploy repo on GitHub: `https://github.com/your-org/opentreasury-deploy`
2. Click **Settings** (top menu bar)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### Set the Secret

On the **Secrets** tab, click **New repository secret** and add:

| Secret name | Where to find the value |
|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | The `AZURE_STATIC_WEB_APPS_API_TOKEN` value from the script output |

> **This is the only secret.** It's a deployment token for the web frontend. All other values are non-sensitive and go in Variables.

### Set the Variables

Click the **Variables** tab, then click **New repository variable** for each:

| Variable name | Where to find the value | What it's for |
|---|---|---|
| `AZURE_CLIENT_ID` | The OIDC app registration client ID from script output | Identifies the deployment service principal |
| `AZURE_TENANT_ID` | The Tenant ID from script output | Your Entra ID tenant |
| `AZURE_SUBSCRIPTION_ID` | The Subscription ID from script output | Your Azure subscription |
| `AZURE_RESOURCE_GROUP` | The resource group name (e.g., `rg-opentreasury-prod`) | Where your Azure resources live |
| `AZURE_WEBAPP_NAME` | The App Service name (e.g., `app-opentreasury-prod`) | Your backend API host |
| `MSAL_CLIENT_ID` | The SPA Client ID from script output | Frontend login configuration |
| `MSAL_API_SCOPE` | `api://opentreasury-api/access_as_user` (uses your project name) | API permission scope |
| `SWA_HOSTNAME` | The SWA hostname from script output (e.g., `blue-coast-abc123.azurestaticapps.net`) | Your web app's address |

> **Double-check every value.** A typo here will cause deployment failures that are hard to diagnose. Copy-paste from the script output whenever possible.

---

## Step 6: Copy template files

Copy the deployment workflow files from the product repo to your deploy repo.

**On macOS/Linux:**
```bash
# From the product repo root
cp -r deploy-template/.github ../opentreasury-deploy/
```

**On Windows (PowerShell):**
```powershell
# From the product repo root
Copy-Item -Recurse deploy-template\.github ..\opentreasury-deploy\
```

Then push the files to GitHub:

```bash
cd ../opentreasury-deploy
git add .
git commit -m "Add deployment workflows"
git push
```

Your deploy repo should now contain:
```
opentreasury-deploy/
└── .github/
    └── workflows/
        ├── deploy.yml           # Deploys the application code
        └── deploy-infra.yml     # Deploys Azure infrastructure changes
```

---

## Step 7: First deployment

The first deployment is a two-step process. After this, you'll only need `deploy.yml` for routine updates.

### Step 7a: Deploy infrastructure

This ensures your Azure infrastructure matches the latest Bicep definitions.

1. Go to your deploy repo on GitHub
2. Click **Actions** (top menu)
3. In the left sidebar, click **Deploy Infrastructure**
4. Click **Run workflow** → leave `product_ref` as `main` (or use a release tag like `v1.0.0`) → click the green **Run workflow** button
5. Wait for it to complete (2–5 minutes)

### Step 7b: Deploy the application

1. Still in **Actions**, click **Deploy** in the left sidebar
2. Click **Run workflow**
3. Set `product_ref` to the version you want to deploy (e.g., `v1.0.0` for the latest release, or `main` for the development version)
4. Click the green **Run workflow** button
5. Wait for it to complete (5–10 minutes)

> **First deployment may take extra time.** Azure needs 5–10 minutes to activate security permissions (RBAC propagation) on the first run. The workflow automatically retries the health check to handle this. Subsequent deployments are much faster.

---

## Step 8: Verify your deployment

Run through this checklist to confirm everything is working:

- [ ] **Web app loads:** Open `https://<your-SWA-hostname>` in your browser. You should see the OpenTreasury login page.
- [ ] **Login works:** Click "Sign in" and authenticate with your organization's Microsoft account. You should land on the dashboard.
- [ ] **API responds:** Open `https://<your-app-service-name>.azurewebsites.net/api/health` in your browser. You should see a JSON response with `"status": "healthy"`.
- [ ] **Workflows succeeded:** Check GitHub Actions — both `Deploy Infrastructure` and `Deploy` should show green checkmarks.

> Replace `<your-SWA-hostname>` with your `SWA_HOSTNAME` value (e.g., `blue-coast-abc123.azurestaticapps.net`) and `<your-app-service-name>` with your `AZURE_WEBAPP_NAME` value (e.g., `app-opentreasury-prod`).

If any of these fail, see [Troubleshooting](#troubleshooting) below.

---

## Getting started after deployment

Congratulations — OpenTreasury is running! Here's how to start using it.

### 1. Assign yourself the Admin role

Before you can manage data, you need the Admin role. OpenTreasury uses Entra ID roles to control access.

1. Go to [portal.azure.com](https://portal.azure.com)
2. In the search bar at the top, type **Enterprise Applications** and select it
3. Find your API app registration (named something like `opentreasury-api-prod`)
   - If you don't see it, change the **Application type** dropdown to **All Applications**
4. Click on it → **Users and groups** (left sidebar)
5. Click **Add user/group**
6. Under **Users**, click **None Selected** → search for your name → select yourself → click **Select**
7. Under **Role**, click **None Selected** → choose **Admin** → click **Select**
8. Click **Assign**

> **Important:** Use **Enterprise Applications**, not **App registrations**. They look similar but serve different purposes. Enterprise Applications is where you assign roles to people.

### 2. Log in for the first time

1. Open your OpenTreasury URL (`https://<your-SWA-hostname>`)
2. Click **Sign in** with your Microsoft account
3. If prompted, consent to the app permissions
4. You should see an empty dashboard — ready to set up

### 3. Create your first bank account

1. Navigate to **Accounts** in the sidebar
2. Click **New Account**
3. Enter the bank name (e.g., "CaixaBank — Main") and the IBAN
4. Click **Save**

Repeat for each bank account your organization uses.

### 4. Set up categories

1. Navigate to **Categories** in the sidebar
2. Create categories that match how your organization classifies spending (e.g., "Therapies", "Office Supplies", "Travel")
3. Add subcategories under each category for finer detail

### 5. Import your first spreadsheet

1. Navigate to **Import** in the sidebar
2. Click **Upload**
3. Select an Excel file exported from your bank
4. Map the columns (date, description, amount) to OpenTreasury's fields
5. Review the preview and click **Import**

---

## Adding users

You can give other people in your organization access to OpenTreasury. There are two roles:

| Role | What they can do |
|---|---|
| **Admin** | Everything — manage transactions, accounts, categories, tags, import data |
| **Viewer** | Read-only — view transactions, reports, and data but cannot change anything |

### To add a user:

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **Enterprise Applications** in the top search bar
3. Find your API app (e.g., `opentreasury-api-prod`)
4. Click **Users and groups** → **Add user/group**
5. Select the user, then select the role (**Admin** or **Viewer**)
6. Click **Assign**

The user can now sign in at your OpenTreasury URL with their organization Microsoft account.

---

## Updating to a new version

The OpenTreasury team releases updates with new features and bug fixes. Here's how to stay current.

### Get notified of new releases

1. Go to [github.com/rett-europe/opentreasury](https://github.com/rett-europe/opentreasury)
2. Click **Watch** (top right) → **Custom** → check **Releases** → click **Apply**

You'll get an email when a new version is published.

### Understanding version numbers

Versions follow a `vMAJOR.MINOR.PATCH` pattern (e.g., `v1.2.3`):

| Change type | Example | What to do |
|---|---|---|
| **PATCH** (v1.2.0 → v1.2.1) | Bug fixes, minor improvements | Just redeploy — safe and quick |
| **MINOR** (v1.2.x → v1.3.0) | New features, no breaking changes | Redeploy — new features available immediately |
| **MAJOR** (v1.x → v2.0.0) | Significant changes, possible data migration | Read the release notes carefully and follow the migration guide |

### Deploy a new version

1. Go to your deploy repo → **Actions** → **Deploy**
2. Click **Run workflow**
3. Set `product_ref` to the new version tag (e.g., `v1.3.0`)
4. Click **Run workflow**

For **MAJOR** version upgrades, also check the release notes for:
- Whether you need to run `Deploy Infrastructure` first (for infrastructure changes)
- Whether there are data migration steps

---

## Rolling back to a previous version

If a new version causes problems, you can instantly go back to the previous working version.

1. Go to your deploy repo → **Actions** → **Deploy**
2. Click **Run workflow**
3. Set `product_ref` to the previous version tag (e.g., `v1.2.0`)
4. Click **Run workflow**

That's it. The previous version is deployed, and your data is unchanged.

---

## Troubleshooting

### "The web app shows a blank page or an error"

**Check:** Did the `Deploy` workflow complete successfully?
1. Go to your deploy repo → **Actions**
2. Look at the most recent `Deploy` run. Is it green (✅)?
3. If it failed, click on it and look at the failing step for error details.

**Fix:** If the workflow failed during the deployment step, try running it again — transient Azure errors sometimes resolve on retry.

### "Login doesn't work / redirect error"

**Check:** Is the SWA hostname registered as a redirect URI?

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **App registrations** → find your SPA app (e.g., `opentreasury-spa-prod`)
3. Click **Authentication** → check that your SWA hostname appears under **Single-page application** redirect URIs
4. It should show: `https://<your-SWA-hostname>`

**Fix:** If the redirect URI is missing, click **Add URI**, paste `https://<your-SWA-hostname>`, and click **Save**. The setup script adds this automatically, but if the SWA wasn't ready when the script ran, it may have been skipped.

### "API returns 500 errors"

**Check:** Are the Key Vault secrets accessible?

1. Go to Azure Portal → search for your App Service (e.g., `app-opentreasury-prod`)
2. Click **Configuration** → **Application settings**
3. Look for settings that start with `@Microsoft.KeyVault(...)` — they should show a green checkmark ✅
4. If they show a red ❌, the App Service can't read from Key Vault

**Fix:** This usually means the App Service's managed identity doesn't have permission to read Key Vault secrets. Re-run the setup script — it will fix the permissions without duplicating resources.

### "Deploy Infrastructure workflow fails"

**Check:** Does the service principal have sufficient permissions?

The infrastructure workflow needs **Contributor** and **User Access Administrator** roles on the resource group. The setup script creates these, but they can take a few minutes to activate.

**Fix:** Wait 5 minutes and try again. If it still fails, check the workflow logs for the specific error message.

### "Health check fails after first deployment"

**This is normal.** On the very first deployment, Azure needs 5–10 minutes to activate security permissions (called RBAC propagation). The health check retries automatically, but if all 3 attempts fail:

**Fix:** Wait 10 minutes, then manually run the `Deploy` workflow again. The permissions will be active by then.

### "Bicep deployment wiped my manual App Service settings"

**This is expected behavior.** The Bicep infrastructure template replaces all App Service settings with the ones defined in the template. Any settings you added manually through the Azure Portal will be removed.

**Fix:** All configuration must go through the Bicep templates. If you need custom settings, add them to your infrastructure definition rather than setting them in the Portal.

### "Cosmos DB Data Explorer says 'Forbidden'"

**This is by design.** OpenTreasury disables Cosmos DB key-based authentication for security. The database only accepts identity-based access (Managed Identity).

**Fix:** To browse your data in the Azure Portal, use the Entra ID-based authentication option in Data Explorer, not a connection string.

---

## Cost monitoring

To keep an eye on what you're spending:

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **Cost Management** in the top search bar
3. Click **Cost analysis** (left sidebar)
4. At the top, set the **Scope** to your resource group (e.g., `rg-opentreasury-prod`)
5. You'll see a breakdown of costs by resource

> **Tip:** Set up a budget alert to get notified if costs exceed a threshold. In Cost Management → **Budgets** → **Add**, set a monthly budget (e.g., €30) and configure email alerts at 80% and 100%.

---

## Tearing down (removing everything)

If you need to completely remove OpenTreasury from your Azure subscription — for example, if you're moving to a different setup or no longer need it — use the teardown script.

> **⚠️ This permanently deletes all your data and resources. This cannot be undone.**

### Back up your data first

Before tearing down, export any data you want to keep using OpenTreasury's export feature (Transactions → Export).

### Run the teardown script

**On macOS/Linux:**
```bash
cd opentreasury
chmod +x scripts/teardown-azure.sh
./scripts/teardown-azure.sh
```

**On Windows (PowerShell):**
```powershell
cd opentreasury
.\scripts\teardown-azure.ps1
```

The script will ask you to type `DELETE` to confirm. It removes:
- The resource group (and everything in it: database, web app, key vault, etc.)
- The Entra ID app registrations
- The service principal

After teardown, you can also delete your GitHub deploy repo if you no longer need it.

---

## Quick reference

| What | Where |
|---|---|
| Your web app | `https://<SWA_HOSTNAME>` |
| API health check | `https://<AZURE_WEBAPP_NAME>.azurewebsites.net/api/health` |
| Azure Portal | [portal.azure.com](https://portal.azure.com) |
| Deploy a new version | Deploy repo → Actions → Deploy → Run workflow |
| Add users | Azure Portal → Enterprise Applications → your app → Users and groups |
| Check costs | Azure Portal → Cost Management → Cost analysis |
| Product releases | [github.com/rett-europe/opentreasury/releases](https://github.com/rett-europe/opentreasury/releases) |
