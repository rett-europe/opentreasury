#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════
# teardown-azure.sh — Delete all Azure resources for OpenTreasury
# ══════════════════════════════════════════════════════════════════════
# Deletes: resource group (all infra), app registrations, service principal.
#
# Usage:
#   chmod +x scripts/teardown-azure.sh
#   ./scripts/teardown-azure.sh
# ══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Variables (must match setup-azure.sh) ───────────────────────────

PROJECT_NAME="opentreasury"          # Must match setup-azure.sh
ENVIRONMENT="prod"                    # Must match setup-azure.sh
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
API_APP_NAME="${PROJECT_NAME}-api-${ENVIRONMENT}"
SPA_APP_NAME="${PROJECT_NAME}-spa-${ENVIRONMENT}"
SP_NAME="sp-${PROJECT_NAME}-github-${ENVIRONMENT}"

# ─── Helpers ─────────────────────────────────────────────────────────

info()  { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()    { echo -e "  \033[1;32m✔ $*\033[0m"; }
warn()  { echo -e "  \033[1;33m⚠ $*\033[0m"; }
err()   { echo -e "  \033[1;31m✖ $*\033[0m" >&2; }

# ─── Login check ─────────────────────────────────────────────────────

info "Checking Azure CLI login..."
if ! az account show &>/dev/null; then
    err "Not logged in. Run 'az login' first."
    exit 1
fi

SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "  Subscription: $SUBSCRIPTION_NAME"

# ─── Confirmation ────────────────────────────────────────────────────

echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
echo "  │  ⚠  THIS WILL DELETE EVERYTHING                            │"
echo "  │                                                             │"
echo "  │  • Resource group: $RESOURCE_GROUP"
echo "  │    (Cosmos DB, App Service, Key Vault, SWA, App Insights)   │"
echo "  │  • App registration: $API_APP_NAME"
echo "  │  • App registration: $SPA_APP_NAME"
echo "  │  • Service principal: $SP_NAME"
echo "  │                                                             │"
echo "  │  This action CANNOT be undone.                              │"
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""
read -r -p "  Type 'DELETE' to confirm: " confirm
if [[ "$confirm" != "DELETE" ]]; then
    echo "  Aborted."
    exit 0
fi

# ─── Delete Resource Group ───────────────────────────────────────────

info "Deleting resource group: $RESOURCE_GROUP"
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    az group delete --name "$RESOURCE_GROUP" --yes --no-wait
    ok "Resource group deletion initiated (runs in background)"
else
    warn "Resource group '$RESOURCE_GROUP' not found — skipping"
fi

# ─── Delete API App Registration ─────────────────────────────────────

info "Deleting API app registration: $API_APP_NAME"
API_OBJECT_ID=$(az ad app list --display-name "$API_APP_NAME" --query "[0].id" -o tsv 2>/dev/null || true)
if [[ -n "$API_OBJECT_ID" && "$API_OBJECT_ID" != "None" ]]; then
    az ad app delete --id "$API_OBJECT_ID"
    ok "API app registration deleted"
else
    warn "App registration '$API_APP_NAME' not found — skipping"
fi

# ─── Delete SPA App Registration ─────────────────────────────────────

info "Deleting SPA app registration: $SPA_APP_NAME"
SPA_OBJECT_ID=$(az ad app list --display-name "$SPA_APP_NAME" --query "[0].id" -o tsv 2>/dev/null || true)
if [[ -n "$SPA_OBJECT_ID" && "$SPA_OBJECT_ID" != "None" ]]; then
    az ad app delete --id "$SPA_OBJECT_ID"
    ok "SPA app registration deleted"
else
    warn "App registration '$SPA_APP_NAME' not found — skipping"
fi

# ─── Delete Service Principal ─────────────────────────────────────────

info "Deleting service principal: $SP_NAME"
SP_OBJECT_ID=$(az ad sp list --display-name "$SP_NAME" --query "[0].id" -o tsv 2>/dev/null || true)
if [[ -n "$SP_OBJECT_ID" && "$SP_OBJECT_ID" != "None" ]]; then
    az ad sp delete --id "$SP_OBJECT_ID"
    ok "Service principal deleted"
else
    warn "Service principal '$SP_NAME' not found — skipping"
fi

# ─── Done ─────────────────────────────────────────────────────────────

info "Teardown complete"
echo ""
echo "  Resource group deletion is running in the background."
echo "  It may take a few minutes for all resources to be fully removed."
echo ""
echo "  Note: Key Vault uses soft-delete (90 days). To purge immediately:"
echo "    az keyvault purge --name kvngotreasury${ENVIRONMENT}"
echo ""
echo "  Don't forget to remove GitHub secrets from your deployment repo."
