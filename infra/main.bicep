// main.bicep — NGO Treasury Infrastructure Orchestrator
// Deploys all Azure resources for the NGO Treasury application.
//
// Usage:
//   az deployment group create \
//     --resource-group rg-ngo-treasury-dev \
//     --template-file infra/main.bicep \
//     --parameters infra/parameters/dev.bicepparam

targetScope = 'resourceGroup'

// ─── Parameters ──────────────────────────────────────────────────────

@allowed(['dev', 'prod'])
@description('Environment name (dev or prod)')
param environmentName string

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Project name used in resource naming')
param projectName string = 'ngo-treasury'

@description('Enable Cosmos DB free tier (one per subscription)')
param cosmosDbEnableFreeTier bool = false

@description('Azure AD Tenant ID for the API app registration')
@secure()
param azureTenantId string

@description('Azure AD Client ID for the API app registration')
@secure()
param azureClientId string

// ─── Variables ───────────────────────────────────────────────────────

var env = environmentName
var tags = {
  project: projectName
  environment: env
}

// Resource naming convention: {type}-{project}-{env}
// Key Vault: 24 char max, no hyphens
var cosmosAccountName = 'cosmos-${projectName}-${env}'
var appServicePlanName = 'plan-${projectName}-${env}'
var appServiceName = 'app-${projectName}-${env}'
var staticWebAppName = 'swa-${projectName}-${env}'
var keyVaultName = 'kv${replace(projectName, '-', '')}${env}' // kvngotreasury{env}
var appInsightsName = 'ai-${projectName}-${env}'
var logAnalyticsName = 'log-${projectName}-${env}'

// ─── Module: Application Insights + Log Analytics ────────────────────
module appInsights 'modules/app-insights.bicep' = {
  name: 'deploy-app-insights'
  params: {
    location: location
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    tags: tags
  }
}

// ─── Module: Cosmos DB ───────────────────────────────────────────────
module cosmosDb 'modules/cosmos-db.bicep' = {
  name: 'deploy-cosmos-db'
  params: {
    location: location
    accountName: cosmosAccountName
    enableFreeTier: cosmosDbEnableFreeTier
    tags: tags
  }
}

// ─── Module: Static Web App ──────────────────────────────────────────
module staticWebApp 'modules/static-web-app.bicep' = {
  name: 'deploy-static-web-app'
  params: {
    location: location
    appName: staticWebAppName
    tags: tags
  }
}

// ─── Module: Key Vault ───────────────────────────────────────────────
module keyVault 'modules/key-vault.bicep' = {
  name: 'deploy-key-vault'
  params: {
    location: location
    vaultName: keyVaultName
    tenantId: subscription().tenantId
    cosmosEndpoint: cosmosDb.outputs.endpoint
    azureTenantId: azureTenantId
    azureClientId: azureClientId
    tags: tags
  }
}

// ─── Module: App Service ─────────────────────────────────────────────
module appService 'modules/app-service.bicep' = {
  name: 'deploy-app-service'
  params: {
    location: location
    planName: appServicePlanName
    appName: appServiceName
    appInsightsInstrumentationKey: appInsights.outputs.instrumentationKey
    appInsightsConnectionString: appInsights.outputs.connectionString
    corsOrigin: staticWebApp.outputs.siteUrl
    keyVaultName: keyVaultName
    tags: tags
  }
}

// ─── Module: Role Assignments ────────────────────────────────────────
module roleAssignments 'modules/role-assignments.bicep' = {
  name: 'deploy-role-assignments'
  params: {
    principalId: appService.outputs.principalId
    cosmosAccountId: cosmosDb.outputs.accountId
    keyVaultId: keyVault.outputs.vaultId
  }
}

// ─── Outputs ─────────────────────────────────────────────────────────

@description('URL of the Angular frontend (Static Web App)')
output staticWebAppUrl string = staticWebApp.outputs.siteUrl

@description('URL of the FastAPI backend (App Service)')
output apiUrl string = appService.outputs.apiUrl

@description('Cosmos DB endpoint')
output cosmosEndpoint string = cosmosDb.outputs.endpoint

@description('Application Insights instrumentation key')
output appInsightsInstrumentationKey string = appInsights.outputs.instrumentationKey

@description('Key Vault URI')
output keyVaultUri string = keyVault.outputs.vaultUri
