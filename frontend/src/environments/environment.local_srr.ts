// Local dev with real backend (no mocks). Configure MSAL with your own Entra ID registration.
export const environment = {
  production: false,
  useMocks: false,
  apiBaseUrl: 'http://localhost:8001/api',
  msal: {
    clientId: 'your-client-id',
    tenantId: 'your-tenant-id',
    authority: 'https://login.microsoftonline.com/your-tenant-id',
    redirectUri: 'http://localhost:4200',
    postLogoutRedirectUri: 'http://localhost:4200',
    apiScope: 'api://your-api-client-id/access_as_user',
  },
};
