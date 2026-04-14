# ======================================================================
# setup-azure.ps1 -- Provision all Azure resources for OpenTreasury
# ======================================================================
# Idempotent: safe to run multiple times.
# Requires: Azure CLI (az), logged in with admin access to Entra ID.
#
# Usage:
#   .\scripts\setup-azure.ps1
# ======================================================================

$ErrorActionPreference = "Stop"

# --- Step 1: Variables (customize these) --------------------------------

$ProjectName     = "opentreasury"                     # Change to your project name
$Environment     = "prod"                              # dev or prod
$Location        = "westeurope"                        # Azure region
$TenantDomain    = "your-tenant.onmicrosoft.com"       # Your Entra ID tenant domain
$ResourceGroup   = "rg-$ProjectName-$Environment"
$GitHubRepo      = "your-org/opentreasury-deploy"      # owner/repo for deployment

# Derived names (match infra/main.bicep naming convention)
$ApiAppName      = "$ProjectName-api-$Environment"
$SpaAppName      = "$ProjectName-spa-$Environment"
$SpName          = "sp-$ProjectName-github-$Environment"
$AppServiceName  = "app-$ProjectName-$Environment"
$SwaName         = "swa-$ProjectName-$Environment"

# --- Helpers ---------------------------------------------------------------

function Write-Info  { param([string]$Msg) Write-Host "`n> $Msg" -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "  [WARN] $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "  [ERR] $Msg" -ForegroundColor Red }

# --- Step 2: Login check -----------------------------------------------

Write-Info "Checking Azure CLI login..."
try {
    $account = az account show | ConvertFrom-Json
} catch {
    Write-Err "Not logged in. Run 'az login' first."
    exit 1
}

# List all available subscriptions and let user pick
$subs = az account list --query "[].{Name:name, Id:id, IsDefault:isDefault}" -o json | ConvertFrom-Json

if ($subs.Count -gt 1) {
    Write-Host ""
    Write-Host "  Available subscriptions:"
    Write-Host ""
    for ($i = 0; $i -lt $subs.Count; $i++) {
        $marker = if ($subs[$i].IsDefault) { " (current)" } else { "" }
        Write-Host ("  [{0}] {1}  ({2}){3}" -f ($i + 1), $subs[$i].Name, $subs[$i].Id, $marker)
    }
    Write-Host ""
    $choice = Read-Host "  Select subscription (1-$($subs.Count), or Enter for current)"

    if ($choice -and $choice -match '^\d+$') {
        $idx = [int]$choice - 1
        if ($idx -ge 0 -and $idx -lt $subs.Count) {
            $selected = $subs[$idx]
            az account set --subscription $selected.Id | Out-Null
            $account = az account show | ConvertFrom-Json
            Write-Ok "Switched to: $($selected.Name)"
        } else {
            Write-Err "Invalid selection."
            exit 1
        }
    }
}

$SubscriptionId   = $account.id
$SubscriptionName = $account.name
$TenantId         = $account.tenantId

Write-Host ""
Write-Host "  Subscription: $SubscriptionName"
Write-Host "  ID:           $SubscriptionId"
Write-Host "  Tenant:       $TenantId"
Write-Host ""

$confirm = Read-Host "  Continue with this subscription? (y/N)"
if ($confirm -notin @("y", "Y")) {
    Write-Host "Aborted."
    exit 0
}

# --- Step 3: Create Resource Group -------------------------------------

Write-Info "Creating resource group: $ResourceGroup"
az group create `
    --name $ResourceGroup `
    --location $Location `
    --tags project=$ProjectName environment=$Environment `
    --output none
Write-Ok "Resource group ready"

# --- Step 4: Backend API App Registration ------------------------------

Write-Info "Creating backend API app registration: $ApiAppName"

$existingApiApp = az ad app list --display-name $ApiAppName --query "[0].appId" -o tsv 2>$null

if ($existingApiApp -and $existingApiApp -ne "None") {
    Write-Warn "App registration '$ApiAppName' already exists (clientId: $existingApiApp). Skipping creation."
    $ApiClientId = $existingApiApp
    $ApiObjectId = az ad app list --display-name $ApiAppName --query "[0].id" -o tsv
    $ApiIdentifierUri = "api://$ApiClientId"
} else {
    # Write app roles to temp file (PowerShell mangles inline JSON for az CLI)
    $appRolesFile = [System.IO.Path]::GetTempFileName()
    @'
[
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
]
'@ | Set-Content -Path $appRolesFile -Encoding UTF8

    # Step 1: Create app WITHOUT identifier URI (Entra ID requires verified domain or app ID in URI)
    $ApiObjectId = az ad app create `
        --display-name $ApiAppName `
        --sign-in-audience "AzureADMyOrg" `
        --app-roles "@$appRolesFile" `
        --query id -o tsv

    Remove-Item $appRolesFile -ErrorAction SilentlyContinue

    if (-not $ApiObjectId) {
        Write-Err "Failed to create API app registration. Check permissions."
        exit 1
    }

    $ApiClientId = az ad app show --id $ApiObjectId --query appId -o tsv

    # Step 2: Now set identifier URI using the app's own client ID (satisfies Entra ID policy)
    $ApiIdentifierUri = "api://$ApiClientId"
    az ad app update --id $ApiObjectId --identifier-uris $ApiIdentifierUri

    # Generate a GUID for the scope
    $scopeId = [guid]::NewGuid().ToString()

    # Expose an API scope via REST API (az ad app update --set doesn't work reliably for oauth2PermissionScopes)
    $scopeFile = [System.IO.Path]::GetTempFileName()
    @"
{
    "api": {
        "oauth2PermissionScopes": [{
            "adminConsentDescription": "Allow the application to access OpenTreasury API on behalf of the signed-in user",
            "adminConsentDisplayName": "Access OpenTreasury API",
            "id": "$scopeId",
            "isEnabled": true,
            "type": "User",
            "userConsentDescription": "Allow the application to access OpenTreasury API on your behalf",
            "userConsentDisplayName": "Access OpenTreasury API",
            "value": "access_as_user"
        }]
    }
}
"@ | Set-Content -Path $scopeFile -Encoding UTF8

    # Wait for Entra ID propagation
    Start-Sleep -Seconds 3

    az rest --method PATCH `
        --uri "https://graph.microsoft.com/v1.0/applications/$ApiObjectId" `
        --headers "Content-Type=application/json" `
        --body "`@$scopeFile"

    Remove-Item $scopeFile -ErrorAction SilentlyContinue

    # Verify the scope was actually created
    $verifyScope = az ad app show --id $ApiObjectId --query "api.oauth2PermissionScopes[0].value" -o tsv 2>$null
    if ($verifyScope -eq "access_as_user") {
        Write-Ok "API scope 'access_as_user' created successfully"
    } else {
        Write-Err "Failed to create API scope. Please create it manually in the Azure Portal:"
        Write-Host "    Entra ID -> App registrations -> $ApiAppName -> Expose an API -> Add a scope"
        Write-Host "    Scope name: access_as_user"
    }

    # Create service principal for the API app
    az ad sp create --id $ApiClientId --output none 2>$null
    if ($LASTEXITCODE -ne 0) { $LASTEXITCODE = 0 } # Ignore if already exists

    Write-Ok "API app registration created"
}

Write-Host "  API Client ID:  $ApiClientId"
Write-Host "  API Object ID:  $ApiObjectId"

# --- Step 5: Frontend SPA App Registration -----------------------------

Write-Info "Creating frontend SPA app registration: $SpaAppName"

$existingSpaApp = az ad app list --display-name $SpaAppName --query "[0].appId" -o tsv 2>$null

if ($existingSpaApp -and $existingSpaApp -ne "None") {
    Write-Warn "App registration '$SpaAppName' already exists (clientId: $existingSpaApp). Skipping creation."
    $SpaClientId = $existingSpaApp
    $SpaObjectId = az ad app list --display-name $SpaAppName --query "[0].id" -o tsv
} else {
    $SpaObjectId = az ad app create `
        --display-name $SpaAppName `
        --sign-in-audience "AzureADMyOrg" `
        --query id -o tsv

    $SpaClientId = az ad app show --id $SpaObjectId --query appId -o tsv

    # Set SPA platform redirect URIs via REST API
    $spaRedirectFile = [System.IO.Path]::GetTempFileName()
    @'
{
    "spa": {
        "redirectUris": ["http://localhost:4200"]
    }
}
'@ | Set-Content -Path $spaRedirectFile -Encoding UTF8

    az rest --method PATCH `
        --uri "https://graph.microsoft.com/v1.0/applications/$SpaObjectId" `
        --headers "Content-Type=application/json" `
        --body "`@$spaRedirectFile"

    Remove-Item $spaRedirectFile -ErrorAction SilentlyContinue

    # Add API permission for backend's access_as_user scope
    $backendScopeId = az ad app show --id $ApiObjectId --query "api.oauth2PermissionScopes[0].id" -o tsv
    az ad app permission add `
        --id $SpaObjectId `
        --api $ApiClientId `
        --api-permissions "${backendScopeId}=Scope"

    # Grant admin consent
    try {
        az ad app permission admin-consent --id $SpaObjectId 2>$null
    } catch {
        Write-Warn "Could not auto-grant admin consent. Grant it manually in the Azure Portal."
    }

    # Create service principal for the SPA app
    az ad sp create --id $SpaClientId --output none 2>$null
    if ($LASTEXITCODE -ne 0) { $LASTEXITCODE = 0 }

    Write-Ok "SPA app registration created"
}

Write-Host "  SPA Client ID:  $SpaClientId"
Write-Host "  SPA Object ID:  $SpaObjectId"

# --- Step 6: Service Principal for GitHub Actions ----------------------

Write-Info "Creating service principal for GitHub Actions: $SpName"

$existingSp = az ad sp list --display-name $SpName --query "[0].appId" -o tsv 2>$null

if ($existingSp -and $existingSp -ne "None") {
    Write-Warn "Service principal '$SpName' already exists. To regenerate credentials, delete it first."
    $SpAppId = $existingSp
    $AzureCredentials = "<existing - regenerate if needed with: az ad sp credential reset --id $SpAppId>"
} else {
    $AzureCredentials = az ad sp create-for-rbac `
        --name $SpName `
        --role Contributor `
        --scopes "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup" `
        --sdk-auth

    $spJson = $AzureCredentials | ConvertFrom-Json
    $SpAppId = $spJson.clientId
    Write-Ok "Service principal created"

    # Add User Access Administrator role (needed for Bicep role assignments)
    az role assignment create `
        --assignee $SpAppId `
        --role "User Access Administrator" `
        --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup" `
        --output none
    Write-Ok "User Access Administrator role assigned"
}

Write-Host "  SP App ID: $SpAppId"

# --- Step 7: Deploy Bicep Infrastructure -------------------------------

Write-Info "Deploying Bicep infrastructure to $ResourceGroup"
Write-Host "  Template:   infra\main.bicep"

az deployment group create `
    --resource-group $ResourceGroup `
    --template-file infra/main.bicep `
    --parameters environmentName=$Environment `
                 location=$Location `
                 projectName=$ProjectName `
                 cosmosDbEnableFreeTier=false `
                 azureTenantId=$TenantId `
                 azureClientId=$ApiClientId `
    --output none

if ($LASTEXITCODE -ne 0) {
    Write-Warn "Bicep deployment had issues. Check Azure Portal for details."
} else {
    Write-Ok "Infrastructure deployed"
}

# --- Step 7b: Populate Key Vault and configure App Service --------------

Write-Info "Populating Key Vault secrets and configuring App Service"

$KvName = "kvngotreasury$Environment"
$CosmosAccountName = "cosmos-$ProjectName-$Environment"

# Get Cosmos endpoint
$CosmosEndpoint = az cosmosdb show --name $CosmosAccountName --resource-group $ResourceGroup --query "documentEndpoint" -o tsv 2>$null
if (-not $CosmosEndpoint) {
    Write-Warn "Could not retrieve Cosmos endpoint. Set it manually later."
    $CosmosEndpoint = "https://$CosmosAccountName.documents.azure.com:443/"
}

# Write secrets to Key Vault
az keyvault secret set --vault-name $KvName --name "AZURE-TENANT-ID" --value $TenantId --output none 2>$null
az keyvault secret set --vault-name $KvName --name "AZURE-CLIENT-ID" --value $ApiClientId --output none 2>$null
az keyvault secret set --vault-name $KvName --name "COSMOS-ENDPOINT" --value $CosmosEndpoint --output none 2>$null
az keyvault secret set --vault-name $KvName --name "COSMOS-DATABASE-NAME" --value "$ProjectName" --output none 2>$null
Write-Ok "Key Vault secrets populated"

# Configure App Service to read from Key Vault + set CORS
az webapp config appsettings set `
    --name "app-$ProjectName-$Environment" `
    --resource-group $ResourceGroup `
    --settings `
        "AZURE_TENANT_ID=@Microsoft.KeyVault(VaultName=$KvName;SecretName=AZURE-TENANT-ID)" `
        "AZURE_CLIENT_ID=@Microsoft.KeyVault(VaultName=$KvName;SecretName=AZURE-CLIENT-ID)" `
        "COSMOS_ENDPOINT=@Microsoft.KeyVault(VaultName=$KvName;SecretName=COSMOS-ENDPOINT)" `
        "COSMOS_DATABASE_NAME=@Microsoft.KeyVault(VaultName=$KvName;SecretName=COSMOS-DATABASE-NAME)" `
        "SCM_DO_BUILD_DURING_DEPLOYMENT=true" `
    --output none
Write-Ok "App Service settings configured with Key Vault references"

# --- Step 8: Get Static Web App Deployment Token -----------------------

Write-Info "Retrieving Static Web App deployment token"

try {
    $SwaToken = az staticwebapp secrets list `
        --name $SwaName `
        --resource-group $ResourceGroup `
        --query "properties.apiKey" -o tsv 2>$null
} catch {
    $SwaToken = $null
}

if (-not $SwaToken) {
    Write-Warn "Could not retrieve SWA token. The Static Web App may not be deployed yet."
    $SwaToken = "<deploy infrastructure first, then re-run>"
}

try {
    $SwaHostname = az staticwebapp show `
        --name $SwaName `
        --resource-group $ResourceGroup `
        --query "defaultHostname" -o tsv 2>$null
} catch {
    $SwaHostname = "<pending>"
}

Write-Ok "SWA hostname: $SwaHostname"

# --- Step 9: Print GitHub Secrets Summary ------------------------------

Write-Info "GitHub Secrets Summary"
Write-Host ""
Write-Host "  Set these in: https://github.com/$GitHubRepo/settings/secrets/actions"
Write-Host ""
Write-Host ("+{0}+{1}+" -f ('-' * 40), ('-' * 39))
Write-Host ("| {0,-38} | {1,-37} |" -f "GitHub Secret", "Value")
Write-Host ("+{0}+{1}+" -f ('-' * 40), ('-' * 39))
Write-Host ("| {0,-38} | {1,-37} |" -f "AZURE_CREDENTIALS",          "<service principal JSON - see above>")
Write-Host ("| {0,-38} | {1,-37} |" -f "AZURE_SUBSCRIPTION_ID",      $SubscriptionId)
Write-Host ("| {0,-38} | {1,-37} |" -f "AZURE_RESOURCE_GROUP",       $ResourceGroup)
Write-Host ("| {0,-38} | {1,-37} |" -f "AZURE_WEBAPP_NAME",          $AppServiceName)
Write-Host ("| {0,-38} | {1,-37} |" -f "AZURE_STATIC_WEB_APPS_API_TOKEN", $SwaToken)
Write-Host ("| {0,-38} | {1,-37} |" -f "MSAL_CLIENT_ID",             $SpaClientId)
Write-Host ("| {0,-38} | {1,-37} |" -f "API_CLIENT_ID",              $ApiClientId)
Write-Host ("+{0}+{1}+" -f ('-' * 40), ('-' * 39))
Write-Host ""

if ($AzureCredentials -and $AzureCredentials -notlike "<existing*") {
    Write-Host "  +---------------------------------------------+"
    Write-Host "  | AZURE_CREDENTIALS JSON (copy this):         |"
    Write-Host "  +---------------------------------------------+"
    Write-Host $AzureCredentials
    Write-Host ""
}

# --- Step 10: Update SWA Redirect URI ----------------------------------

Write-Info "Updating SPA redirect URIs with SWA hostname"

if ($SwaHostname -ne "<pending>") {
    $swaRedirectFile = [System.IO.Path]::GetTempFileName()
    @"
{
    "spa": {
        "redirectUris": ["http://localhost:4200", "https://$SwaHostname"]
    }
}
"@ | Set-Content -Path $swaRedirectFile -Encoding UTF8

    az rest --method PATCH `
        --uri "https://graph.microsoft.com/v1.0/applications/$SpaObjectId" `
        --headers "Content-Type=application/json" `
        --body "`@$swaRedirectFile"

    Remove-Item $swaRedirectFile -ErrorAction SilentlyContinue
    Write-Ok "SPA redirect URIs updated: http://localhost:4200, https://$SwaHostname"
} else {
    Write-Warn "SWA not yet deployed. Run this script again after deploying infrastructure."
}

# --- Step 11: Next Steps -----------------------------------------------

Write-Info "Setup complete! Next steps:"
Write-Host ""
Write-Host "  1. Set GitHub Secrets:"
Write-Host "     Go to https://github.com/$GitHubRepo/settings/secrets/actions"
Write-Host "     Add each secret from the table above."
Write-Host ""
Write-Host "  2. Update frontend\src\environments\environment.prod.ts:"
Write-Host "     clientId:  '$SpaClientId'"
Write-Host "     tenantId:  '$TenantId'"
Write-Host "     authority: 'https://login.microsoftonline.com/$TenantId'"
Write-Host "     apiScope:  '$ApiIdentifierUri/access_as_user'"
Write-Host "     redirectUri: 'https://$SwaHostname'"
Write-Host ""
Write-Host "  3. Push to main (or merge a PR) to trigger CI/CD."
Write-Host ""
Write-Host "  Done!"
