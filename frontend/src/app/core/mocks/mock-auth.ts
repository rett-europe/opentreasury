/**
 * Mock MSAL providers for offline development.
 * Replaces real Azure AD authentication with hardcoded admin user.
 */
import { Injectable, Provider } from '@angular/core';
import {
  HTTP_INTERCEPTORS,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import {
  MSAL_GUARD_CONFIG,
  MSAL_INSTANCE,
  MSAL_INTERCEPTOR_CONFIG,
  MsalBroadcastService,
  MsalGuard,
  MsalService,
} from '@azure/msal-angular';
import { Observable, of, Subject, BehaviorSubject } from 'rxjs';
import { InteractionStatus, AccountInfo, IPublicClientApplication } from '@azure/msal-browser';

// ---------------------------------------------------------------------------
// Mock account that all MSAL stubs return
// ---------------------------------------------------------------------------
const MOCK_ACCOUNT: AccountInfo = {
  homeAccountId: 'mock-home-id',
  localAccountId: 'mock-oid-pedro',
  environment: 'mock',
  tenantId: 'mock-tenant',
  username: 'demo@example.org',
  name: 'Demo Admin',
};

// ---------------------------------------------------------------------------
// Stub MsalService
// ---------------------------------------------------------------------------
@Injectable()
class MockMsalService {
  instance = {
    getAllAccounts: () => [MOCK_ACCOUNT],
    getActiveAccount: () => MOCK_ACCOUNT,
    setActiveAccount: () => { /* no-op in mock */ },
    acquireTokenSilent: () => Promise.resolve({ accessToken: 'mock-token' }),
  } as unknown as IPublicClientApplication;

  handleRedirectObservable() {
    return of(null);
  }

  loginRedirect() {
    console.log('[MOCK AUTH] loginRedirect() called — no-op in mock mode');
  }

  logoutRedirect() {
    console.log('[MOCK AUTH] logoutRedirect() called — no-op in mock mode');
  }
}

// ---------------------------------------------------------------------------
// Stub MsalBroadcastService — emits InteractionStatus.None immediately
// ---------------------------------------------------------------------------
@Injectable()
class MockMsalBroadcastService {
  readonly inProgress$ = new BehaviorSubject<InteractionStatus>(InteractionStatus.None);
  readonly msalSubject$ = new Subject<unknown>();
}

// ---------------------------------------------------------------------------
// Stub MsalGuard — always allows navigation
// ---------------------------------------------------------------------------
@Injectable()
class MockMsalGuard {
  canActivate(): boolean {
    return true;
  }

  canActivateChild(): boolean {
    return true;
  }

  canLoad(): boolean {
    return true;
  }
}

// ---------------------------------------------------------------------------
// Stub MsalInterceptor — passes requests through without adding tokens
// ---------------------------------------------------------------------------
@Injectable()
class MockMsalInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, handler: HttpHandler): Observable<HttpEvent<unknown>> {
    return handler.handle(req);
  }
}

// ---------------------------------------------------------------------------
// Provider array — drop-in replacement for the real MSAL providers
// ---------------------------------------------------------------------------
export function getMockAuthProviders(): Provider[] {
  return [
    { provide: MsalService, useClass: MockMsalService },
    { provide: MsalGuard, useClass: MockMsalGuard },
    { provide: MsalBroadcastService, useClass: MockMsalBroadcastService },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: MockMsalInterceptor,
      multi: true,
    },
    // MSAL factories still needed as injection tokens — provide no-ops
    { provide: MSAL_INSTANCE, useFactory: () => new MockMsalService().instance },
    { provide: MSAL_GUARD_CONFIG, useValue: { interactionType: 0 } },
    { provide: MSAL_INTERCEPTOR_CONFIG, useValue: { interactionType: 0, protectedResourceMap: new Map() } },
  ];
}
