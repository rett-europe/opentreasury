using '../main.bicep'

param environmentName = 'dev'
param location = 'westeurope'           // Change to your preferred Azure region
param projectName = 'opentreasury'      // Change to your project name
param cosmosDbEnableFreeTier = true      // One free tier per subscription
