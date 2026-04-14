# Frontend — OpenTreasury (Angular)

## Prerequisites

- Node.js 20+
- npm 10+

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm start
```

Runs at `http://localhost:4200`.

## Build

```bash
npm run build
```

Output in `dist/opentreasury/`.

## Configuration

Copy `.env.example` and fill in the values for your environment. The actual configuration lives in `src/environments/environment.ts` (dev) and `environment.prod.ts` (production).

### Required MSAL settings:
- `clientId` — App Registration client ID from Entra ID
- `tenantId` — your Entra ID tenant ID
- `redirectUri` — Must match the redirect URI configured in App Registration
- `apiScope` — The API scope exposed by the backend App Registration
