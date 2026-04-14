# ══════════════════════════════════════════════════════════════════════
# teardown-azure.ps1 — Delete all Azure resources for OpenTreasury
# ══════════════════════════════════════════════════════════════════════
# Deletes: resource group (all infra), app registrations, service principal.
#
# Usage:
#   .\scripts\teardown-azure.ps1
# ══════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ─── Variables (must match setup-azure.ps1) ──────────────────────────

$ProjectName   = "opentreasury"                     # Must match setup-azure.ps1
$Environment   = "prod"                              # Must match setup-azure.ps1
$ResourceGroup = "rg-$ProjectName-$Environment"
$ApiAppName    = "$ProjectName-api-$Environment"
$SpaAppName    = "$ProjectName-spa-$Environment"
$SpName        = "sp-$ProjectName-github-$Environment"

# ─── Helpers ─────────────────────────────────────────────────────────

function Write-Info  { param([string]$Msg) Write-Host "`n▶ $Msg" -ForegroundColor Blue }
function Write-Ok    { param([string]$Msg) Write-Host "  ✔ $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "  ⚠ $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "  ✖ $Msg" -ForegroundColor Red }

# ─── Login check ─────────────────────────────────────────────────────

Write-Info "Checking Azure CLI login..."
try {
    $account = az account show | ConvertFrom-Json
} catch {
    Write-Err "Not logged in. Run 'az login' first."
    exit 1
}

Write-Host "  Subscription: $($account.name)"

# ─── Confirmation ────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────────────┐"
Write-Host "  │  ⚠  THIS WILL DELETE EVERYTHING                            │"
Write-Host "  │                                                             │"
Write-Host "  │  • Resource group: $ResourceGroup"
Write-Host "  │    (Cosmos DB, App Service, Key Vault, SWA, App Insights)   │"
Write-Host "  │  • App registration: $ApiAppName"
Write-Host "  │  • App registration: $SpaAppName"
Write-Host "  │  • Service principal: $SpName"
Write-Host "  │                                                             │"
Write-Host "  │  This action CANNOT be undone.                              │"
Write-Host "  └─────────────────────────────────────────────────────────────┘"
Write-Host ""

$confirm = Read-Host "  Type 'DELETE' to confirm"
if ($confirm -ne "DELETE") {
    Write-Host "  Aborted."
    exit 0
}

# ─── Delete Resource Group ───────────────────────────────────────────

Write-Info "Deleting resource group: $ResourceGroup"
$rgExists = az group show --name $ResourceGroup 2>$null
if ($rgExists) {
    az group delete --name $ResourceGroup --yes --no-wait
    Write-Ok "Resource group deletion initiated (runs in background)"
} else {
    Write-Warn "Resource group '$ResourceGroup' not found - skipping"
}

# ─── Delete API App Registration ─────────────────────────────────────

Write-Info "Deleting API app registration: $ApiAppName"
$apiObjectId = az ad app list --display-name $ApiAppName --query "[0].id" -o tsv 2>$null
if ($apiObjectId -and $apiObjectId -ne "None") {
    az ad app delete --id $apiObjectId
    Write-Ok "API app registration deleted"
} else {
    Write-Warn "App registration '$ApiAppName' not found - skipping"
}

# ─── Delete SPA App Registration ─────────────────────────────────────

Write-Info "Deleting SPA app registration: $SpaAppName"
$spaObjectId = az ad app list --display-name $SpaAppName --query "[0].id" -o tsv 2>$null
if ($spaObjectId -and $spaObjectId -ne "None") {
    az ad app delete --id $spaObjectId
    Write-Ok "SPA app registration deleted"
} else {
    Write-Warn "App registration '$SpaAppName' not found - skipping"
}

# ─── Delete Service Principal ─────────────────────────────────────────

Write-Info "Deleting service principal: $SpName"
$spObjectId = az ad sp list --display-name $SpName --query "[0].id" -o tsv 2>$null
if ($spObjectId -and $spObjectId -ne "None") {
    az ad sp delete --id $spObjectId
    Write-Ok "Service principal deleted"
} else {
    Write-Warn "Service principal '$SpName' not found - skipping"
}

# ─── Done ─────────────────────────────────────────────────────────────

Write-Info "Teardown complete"
Write-Host ""
Write-Host "  Resource group deletion is running in the background."
Write-Host "  It may take a few minutes for all resources to be fully removed."
Write-Host ""
Write-Host "  Note: Key Vault uses soft-delete (90 days). To purge immediately:"
Write-Host "    az keyvault purge --name kvngotreasury$Environment"
Write-Host ""
Write-Host "  Don't forget to remove GitHub secrets from your deployment repo."
