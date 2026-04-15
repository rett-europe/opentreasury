export const environment = {
  production: false,
  useMocks: false,
  apiBaseUrl: 'http://localhost:8000/api',
  msal: {
    clientId: 'ada09dc2-4837-4b65-a071-79adef8eb2f6',
    tenantId: 'c0114a74-bb01-45ae-8ba9-0b8488926b7b',
    authority: 'https://login.microsoftonline.com/c0114a74-bb01-45ae-8ba9-0b8488926b7b',
    redirectUri: 'http://localhost:4200',
    postLogoutRedirectUri: 'http://localhost:4200',
    apiScope: 'api://881e9b40-6d5a-4eca-b4ef-4700cab2adb7/access_as_user',
  },
};
