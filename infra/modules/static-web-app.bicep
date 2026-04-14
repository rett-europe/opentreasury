// static-web-app.bicep — Azure Static Web App for Angular frontend
// NGO Treasury

@description('Azure region')
param location string

@description('Name of the Static Web App')
param appName string

@description('Tags to apply to all resources')
param tags object

// ─── Static Web App ──────────────────────────────────────────────────
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: appName
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    buildProperties: {
      appLocation: 'frontend'
      outputLocation: 'dist/frontend/browser'
    }
  }
}

// ─── Outputs ─────────────────────────────────────────────────────────
output staticWebAppId string = staticWebApp.id
output staticWebAppName string = staticWebApp.name
output defaultHostname string = staticWebApp.properties.defaultHostname
output siteUrl string = 'https://${staticWebApp.properties.defaultHostname}'
