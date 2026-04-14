// cosmos-db.bicep — Cosmos DB Account (Serverless, NoSQL) + Database + Containers
// OpenTreasury

@description('Azure region for the Cosmos DB account')
param location string

@description('Name of the Cosmos DB account')
param accountName string

@description('Enable free tier (only one per subscription)')
param enableFreeTier bool = false

@description('Name of the Cosmos DB database')
param databaseName string

@description('Tags to apply to all resources')
param tags object

// ─── Cosmos DB Account ───────────────────────────────────────────────
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: enableFreeTier
    capabilities: [
      { name: 'EnableServerless' }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    disableLocalAuth: true // Managed Identity only — no connection string/key auth
  }
}

// ─── Database ────────────────────────────────────────────────────────
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// ─── Container: transactions ─────────────────────────────────────────
resource transactionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'transactions'
  properties: {
    resource: {
      id: 'transactions'
      partitionKey: {
        paths: ['/partitionKey']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/date/*' }
          { path: '/accountId/*' }
          { path: '/categoryId/*' }
          { path: '/subcategoryId/*' }
          { path: '/tagIds/[]/*' }
          { path: '/amount/*' }
          { path: '/year/*' }
          { path: '/month/*' }
          { path: '/isDeleted/*' }
        ]
        excludedPaths: [
          { path: '/bankDescription/*' }
          { path: '/detail/*' }
          { path: '/invoiceReference/*' }
          { path: '/createdByName/*' }
          { path: '/updatedByName/*' }
          { path: '/*' }
          { path: '/"_etag"/?' }
        ]
        compositeIndexes: [
          [
            { path: '/date', order: 'descending' }
            { path: '/accountId', order: 'ascending' }
          ]
        ]
      }
    }
  }
}

// ─── Container: categories ───────────────────────────────────────────
resource categoriesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'categories'
  properties: {
    resource: {
      id: 'categories'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
        version: 2
      }
      // Default indexing — small container, index everything
    }
  }
}

// ─── Container: reference_data ───────────────────────────────────────
resource referenceDataContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'reference_data'
  properties: {
    resource: {
      id: 'reference_data'
      partitionKey: {
        paths: ['/type']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/type/*' }
          { path: '/isActive/*' }
          { path: '/sortOrder/*' }
        ]
        excludedPaths: [
          { path: '/*' }
          { path: '/"_etag"/?' }
        ]
      }
    }
  }
}

// ─── Container: audit_log ────────────────────────────────────────────
resource auditLogContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'audit_log'
  properties: {
    resource: {
      id: 'audit_log'
      partitionKey: {
        paths: ['/entityType']
        kind: 'Hash'
        version: 2
      }
      defaultTtl: 220752000 // 7 years in seconds
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/entityType/*' }
          { path: '/entityId/*' }
          { path: '/changedAt/*' }
        ]
        excludedPaths: [
          { path: '/*' }
          { path: '/"_etag"/?' }
        ]
      }
    }
  }
}

// ─── Outputs ─────────────────────────────────────────────────────────
output accountId string = cosmosAccount.id
output accountName string = cosmosAccount.name
output endpoint string = cosmosAccount.properties.documentEndpoint
output principalId string = '' // Cosmos DB doesn't have MSI; consumers use their own identity
