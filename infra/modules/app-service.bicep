// app-service.bicep — App Service Plan (B1 Linux) + Web App (Python 3.12)
// OpenTreasury

@description('Azure region')
param location string

@description('Name of the App Service Plan')
param planName string

@description('Name of the Web App')
param appName string

@description('Application Insights instrumentation key')
param appInsightsInstrumentationKey string

@description('Application Insights connection string')
param appInsightsConnectionString string

@description('Allowed CORS origin (Static Web App URL)')
param corsOrigin string

@description('Key Vault name for secret references')
param keyVaultName string

@description('Cosmos DB database name')
param cosmosDatabaseName string

@description('Tags to apply to all resources')
param tags object

// ─── App Service Plan ────────────────────────────────────────────────
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

// ─── Web App ─────────────────────────────────────────────────────────
resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: [
          corsOrigin
        ]
        supportCredentials: true
      }
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'COSMOS_ENDPOINT'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=cosmos-endpoint)'
        }
        {
          name: 'COSMOS_DATABASE_NAME'
          value: cosmosDatabaseName
        }
        {
          name: 'AZURE_TENANT_ID'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=azure-tenant-id)'
        }
        {
          name: 'ENTRA_API_CLIENT_ID'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=entra-api-client-id)'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsightsInstrumentationKey
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
      ]
    }
  }
}

// ─── Outputs ─────────────────────────────────────────────────────────
output appServiceId string = webApp.id
output appServiceName string = webApp.name
output defaultHostname string = webApp.properties.defaultHostName
output principalId string = webApp.identity.principalId
output apiUrl string = 'https://${webApp.properties.defaultHostName}'
