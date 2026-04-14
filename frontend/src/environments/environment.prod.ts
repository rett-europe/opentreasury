// Production values are injected by CI/CD pipeline (GitHub Actions).
// Placeholders below are replaced at build time via environment substitution.
// See .github/workflows/deploy-prod.yml for the replacement step.
export const environment = {
  production: true,
  useMocks: false,
  apiBaseUrl: '#{API_BASE_URL}#',
  msal: {
    clientId: '#{MSAL_CLIENT_ID}#',
    tenantId: '#{MSAL_TENANT_ID}#',
    authority: 'https://login.microsoftonline.com/#{MSAL_TENANT_ID}#',
    redirectUri: '#{SWA_URL}#',
    postLogoutRedirectUri: '#{SWA_URL}#',
    apiScope: '#{MSAL_API_SCOPE}#',
  },
};
