export const environment = {
  production: false,
  useMocks: true,
  apiBaseUrl: 'http://localhost:8000/api',
  msal: {
    clientId: 'your-client-id',
    tenantId: 'your-tenant-id',
    authority: 'https://login.microsoftonline.com/your-tenant-id',
    redirectUri: 'http://localhost:4200',
    postLogoutRedirectUri: 'http://localhost:4200',
    apiScope: 'api://your-api-client-id/access_as_user',
  },
};
