// role-assignments.bicep — RBAC assignments for App Service Managed Identity
// NGO Treasury

@description('Principal ID of the App Service Managed Identity')
param principalId string

@description('Resource ID of the Cosmos DB account')
param cosmosAccountId string

@description('Resource ID of the Key Vault')
param keyVaultId string

// ─── Built-in Role Definitions ───────────────────────────────────────
// Cosmos DB Built-in Data Contributor: 00000000-0000-0000-0000-000000000002
// This is the Cosmos DB data-plane RBAC role (not ARM-level)
// For Cosmos DB data plane RBAC, we use the SQL role assignment resource instead.

// Key Vault Secrets User: 4633458b-17de-408a-b874-0445c86b69e6
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

// ─── Cosmos DB Data Plane RBAC ───────────────────────────────────────
// The Cosmos DB Built-in Data Contributor role ID is a fixed GUID
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: last(split(cosmosAccountId, '/'))
}

resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccountId, principalId, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: '${cosmosAccountId}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: principalId
    scope: cosmosAccountId
  }
}

// ─── Key Vault Secrets User ──────────────────────────────────────────
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultId, principalId, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: last(split(keyVaultId, '/'))
}
