// key-vault.bicep — Azure Key Vault + Secrets
// NGO Treasury

@description('Azure region')
param location string

@description('Name of the Key Vault')
param vaultName string

@description('Tenant ID for the Key Vault')
param tenantId string

@description('Cosmos DB endpoint to store as secret')
param cosmosEndpoint string

@description('Azure AD Tenant ID for the API app registration')
@secure()
param azureTenantId string

@description('Azure AD Client ID for the API app registration')
@secure()
param azureClientId string

@description('Tags to apply to all resources')
param tags object

// ─── Key Vault ───────────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
  }
}

// ─── Secrets ─────────────────────────────────────────────────────────
resource cosmosEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmos-endpoint'
  properties: {
    value: cosmosEndpoint
  }
}

resource tenantIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-tenant-id'
  properties: {
    value: azureTenantId
  }
}

resource clientIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-client-id'
  properties: {
    value: azureClientId
  }
}

// ─── Outputs ─────────────────────────────────────────────────────────
output vaultId string = keyVault.id
output vaultName string = keyVault.name
output vaultUri string = keyVault.properties.vaultUri
