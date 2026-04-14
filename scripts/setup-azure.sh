#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════
# setup-azure.sh — Provision all Azure resources for NGO Treasury
# ══════════════════════════════════════════════════════════════════════
# Idempotent: safe to run multiple times.
# Requires: Azure CLI (az), logged in with admin access to Entra ID.
#
# Usage:
#   chmod +x scripts/setup-azure.sh
#   ./scripts/setup-azure.sh
# ══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Step 1: Variables (customize these) ─────────────────────────────

PROJECT_NAME="opentreasury"          # Change to your project name
ENVIRONMENT="prod"                    # dev or prod
LOCATION="westeurope"                 # Azure region
TENANT_DOMAIN="your-tenant.onmicrosoft.com"  # Your Entra ID tenant domain
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
GITHUB_REPO="your-org/opentreasury-deploy"   # owner/repo for deployment

# Derived names (match infra/main.bicep naming convention)
API_APP_NAME="${PROJECT_NAME}-api-${ENVIRONMENT}"
SPA_APP_NAME="${PROJECT_NAME}-spa-${ENVIRONMENT}"
SP_NAME="sp-${PROJECT_NAME}-github-${ENVIRONMENT}"
APP_SERVICE_NAME="app-${PROJECT_NAME}-${ENVIRONMENT}"
SWA_NAME="swa-${PROJECT_NAME}-${ENVIRONMENT}"

# ─── Helpers ─────────────────────────────────────────────────────────

info()  { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()    { echo -e "  \033[1;32m✔ $*\033[0m"; }
warn()  { echo -e "  \033[1;33m⚠ $*\033[0m"; }
err()   { echo -e "  \033[1;31m✖ $*\033[0m" >&2; }

# ─── Step 2: Login check ─────────────────────────────────────────────

info "Checking Azure CLI login..."
if ! az account show &>/dev/null; then
    err "Not logged in. Run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo ""
echo "  Subscription: $SUBSCRIPTION_NAME"
echo "  ID:           $SUBSCRIPTION_ID"
echo "  Tenant:       $TENANT_ID"
echo ""
read -r -p "  Continue with this subscription? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted. Use 'az account set --subscription <id>' to switch."
    exit 0
fi

# ─── Step 3: Create Resource Group ───────────────────────────────────

info "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags project="$PROJECT_NAME" environment="$ENVIRONMENT" \
    --output none
ok "Resource group ready"

# ─── Step 4: Backend API App Registration ────────────────────────────

info "Creating backend API app registration: $API_APP_NAME"

API_IDENTIFIER_URI="api://${PROJECT_NAME}-api"

# Check if app already exists
EXISTING_API_APP=$(az ad app list --display-name "$API_APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_API_APP" && "$EXISTING_API_APP" != "None" ]]; then
    warn "App registration '$API_APP_NAME' already exists (clientId: $EXISTING_API_APP). Skipping creation."
    API_CLIENT_ID="$EXISTING_API_APP"
    API_OBJECT_ID=$(az ad app list --display-name "$API_APP_NAME" --query "[0].id" -o tsv)
else
    # Define app roles
    APP_ROLES='[
        {
            "allowedMemberTypes": ["User"],
            "description": "Admins can read and write all data",
            "displayName": "Admin",
            "isEnabled": true,
            "value": "Admin"
        },
        {
            "allowedMemberTypes": ["User"],
            "description": "Viewers can read data only (default for users without explicit role)",
            "displayName": "Viewer",
            "isEnabled": true,
            "value": "Viewer"
        }
    ]'

    # Create the app registration
    API_OBJECT_ID=$(az ad app create \
        --display-name "$API_APP_NAME" \
        --sign-in-audience "AzureADMyOrg" \
        --identifier-uris "$API_IDENTIFIER_URI" \
        --app-roles "$APP_ROLES" \
        --query id -o tsv)

    API_CLIENT_ID=$(az ad app show --id "$API_OBJECT_ID" --query appId -o tsv)

    # Expose an API scope: access_as_user
    # Generate a GUID for the scope ID
    SCOPE_ID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || uuidgen || cat /proc/sys/kernel/random/uuid)

    az ad app update --id "$API_OBJECT_ID" \
        --set "api.oauth2PermissionScopes=[{
            \"adminConsentDescription\": \"Allow the application to access NGO Treasury API on behalf of the signed-in user\",
            \"adminConsentDisplayName\": \"Access NGO Treasury API\",
            \"id\": \"$SCOPE_ID\",
            \"isEnabled\": true,
            \"type\": \"User\",
            \"userConsentDescription\": \"Allow the application to access NGO Treasury API on your behalf\",
            \"userConsentDisplayName\": \"Access NGO Treasury API\",
            \"value\": \"access_as_user\"
        }]"

    # Create service principal for the API app (required for consent)
    az ad sp create --id "$API_CLIENT_ID" --output none 2>/dev/null || true

    ok "API app registration created"
fi

echo "  API Client ID:  $API_CLIENT_ID"
echo "  API Object ID:  $API_OBJECT_ID"

# ─── Step 5: Frontend SPA App Registration ───────────────────────────

info "Creating frontend SPA app registration: $SPA_APP_NAME"

EXISTING_SPA_APP=$(az ad app list --display-name "$SPA_APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_SPA_APP" && "$EXISTING_SPA_APP" != "None" ]]; then
    warn "App registration '$SPA_APP_NAME' already exists (clientId: $EXISTING_SPA_APP). Skipping creation."
    SPA_CLIENT_ID="$EXISTING_SPA_APP"
    SPA_OBJECT_ID=$(az ad app list --display-name "$SPA_APP_NAME" --query "[0].id" -o tsv)
else
    # Create the SPA app with redirect URIs
    SPA_OBJECT_ID=$(az ad app create \
        --display-name "$SPA_APP_NAME" \
        --sign-in-audience "AzureADMyOrg" \
        --query id -o tsv)

    SPA_CLIENT_ID=$(az ad app show --id "$SPA_OBJECT_ID" --query appId -o tsv)

    # Set SPA platform redirect URIs
    az ad app update --id "$SPA_OBJECT_ID" \
        --spa-redirect-uris "http://localhost:4200"

    # Add API permission for backend's access_as_user scope
    # Permission format: resourceAppId + scope ID
    BACKEND_SCOPE_ID=$(az ad app show --id "$API_OBJECT_ID" --query "api.oauth2PermissionScopes[0].id" -o tsv)
    az ad app permission add \
        --id "$SPA_OBJECT_ID" \
        --api "$API_CLIENT_ID" \
        --api-permissions "${BACKEND_SCOPE_ID}=Scope"

    # Grant admin consent
    az ad app permission admin-consent --id "$SPA_OBJECT_ID" 2>/dev/null || \
        warn "Could not auto-grant admin consent. Grant it manually in the Azure Portal."

    # Create service principal for the SPA app
    az ad sp create --id "$SPA_CLIENT_ID" --output none 2>/dev/null || true

    ok "SPA app registration created"
fi

echo "  SPA Client ID:  $SPA_CLIENT_ID"
echo "  SPA Object ID:  $SPA_OBJECT_ID"

# ─── Step 6: Service Principal for GitHub Actions ────────────────────

info "Creating service principal for GitHub Actions: $SP_NAME"

EXISTING_SP=$(az ad sp list --display-name "$SP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_SP" && "$EXISTING_SP" != "None" ]]; then
    warn "Service principal '$SP_NAME' already exists. To regenerate credentials, delete it first."
    SP_APP_ID="$EXISTING_SP"
    AZURE_CREDENTIALS="<existing — regenerate if needed with: az ad sp credential reset --id $SP_APP_ID>"
else
    AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role Contributor \
        --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
        --sdk-auth)

    SP_APP_ID=$(echo "$AZURE_CREDENTIALS" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientId'])" 2>/dev/null || true)
    ok "Service principal created"
fi

echo "  SP App ID: $SP_APP_ID"

# ─── Step 7: Deploy Bicep Infrastructure ─────────────────────────────

info "Deploying Bicep infrastructure to $RESOURCE_GROUP"
echo "  Template:   infra/main.bicep"
echo "  Parameters: infra/parameters/${ENVIRONMENT}.bicepparam"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters "infra/parameters/${ENVIRONMENT}.bicepparam" \
    --parameters azureTenantId="$TENANT_ID" azureClientId="$API_CLIENT_ID" \
    --output none

ok "Infrastructure deployed"

# ─── Step 8: Get Static Web App Deployment Token ─────────────────────

info "Retrieving Static Web App deployment token"

SWA_TOKEN=$(az staticwebapp secrets list \
    --name "$SWA_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.apiKey" -o tsv 2>/dev/null || true)

if [[ -z "$SWA_TOKEN" ]]; then
    warn "Could not retrieve SWA token. The Static Web App may not be deployed yet."
    SWA_TOKEN="<deploy infrastructure first, then re-run>"
fi

SWA_HOSTNAME=$(az staticwebapp show \
    --name "$SWA_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "defaultHostname" -o tsv 2>/dev/null || echo "<pending>")

ok "SWA hostname: $SWA_HOSTNAME"

# ─── Step 9: Print GitHub Secrets Summary ────────────────────────────

info "GitHub Secrets Summary"
echo ""
echo "  Set these in: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo ""
echo "╔════════════════════════════════════════╦═══════════════════════════════════════╗"
echo "║ GitHub Secret                          ║ Value                                 ║"
echo "╠════════════════════════════════════════╬═══════════════════════════════════════╣"
printf "║ %-38s ║ %-37s ║\n" "AZURE_CREDENTIALS"          "<service principal JSON — see above>"
printf "║ %-38s ║ %-37s ║\n" "AZURE_SUBSCRIPTION_ID"      "$SUBSCRIPTION_ID"
printf "║ %-38s ║ %-37s ║\n" "AZURE_RESOURCE_GROUP"       "$RESOURCE_GROUP"
printf "║ %-38s ║ %-37s ║\n" "AZURE_WEBAPP_NAME"          "$APP_SERVICE_NAME"
printf "║ %-38s ║ %-37s ║\n" "AZURE_STATIC_WEB_APPS_API_TOKEN" "$SWA_TOKEN"
printf "║ %-38s ║ %-37s ║\n" "MSAL_CLIENT_ID"             "$SPA_CLIENT_ID"
printf "║ %-38s ║ %-37s ║\n" "API_CLIENT_ID"              "$API_CLIENT_ID"
echo "╚════════════════════════════════════════╩═══════════════════════════════════════╝"
echo ""

if [[ "$AZURE_CREDENTIALS" != "<existing"* ]]; then
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │ AZURE_CREDENTIALS JSON (copy this):         │"
    echo "  └─────────────────────────────────────────────┘"
    echo "$AZURE_CREDENTIALS"
    echo ""
fi

# ─── Step 10: Update SWA Redirect URI ────────────────────────────────

info "Updating SPA redirect URIs with SWA hostname"

if [[ "$SWA_HOSTNAME" != "<pending>" ]]; then
    az ad app update --id "$SPA_OBJECT_ID" \
        --spa-redirect-uris "http://localhost:4200" "https://${SWA_HOSTNAME}"
    ok "SPA redirect URIs updated: http://localhost:4200, https://${SWA_HOSTNAME}"
else
    warn "SWA not yet deployed. Update redirect URIs later:"
    echo "  az ad app update --id $SPA_OBJECT_ID --spa-redirect-uris \"http://localhost:4200\" \"https://<swa-hostname>\""
fi

# ─── Step 11: Next Steps ─────────────────────────────────────────────

info "Setup complete! Next steps:"
echo ""
echo "  1. Set GitHub Secrets:"
echo "     Go to https://github.com/${GITHUB_REPO}/settings/secrets/actions"
echo "     Add each secret from the table above."
echo ""
echo "  2. Update frontend/src/environments/environment.prod.ts:"
echo "     clientId:  '$SPA_CLIENT_ID'"
echo "     tenantId:  '$TENANT_ID'"
echo "     authority: 'https://login.microsoftonline.com/$TENANT_ID'"
echo "     apiScope:  '${API_IDENTIFIER_URI}/access_as_user'"
echo "     redirectUri: 'https://${SWA_HOSTNAME}'"
echo ""
echo "  3. Push to main (or merge a PR) to trigger CI/CD."
echo ""
echo "  Done! 🎉"
