import {
  ApplicationConfig,
  APP_INITIALIZER,
  Provider,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import {
  provideHttpClient,
  withInterceptors,
  withInterceptorsFromDi,
  HTTP_INTERCEPTORS,
} from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideNativeDateAdapter } from '@angular/material/core';
import {
  MSAL_GUARD_CONFIG,
  MSAL_INSTANCE,
  MSAL_INTERCEPTOR_CONFIG,
  MsalBroadcastService,
  MsalGuard,
  MsalInterceptor,
  MsalService,
} from '@azure/msal-angular';
import { environment } from '@env/environment';
import { routes } from './app.routes';
import {
  msalInstanceFactory,
  msalGuardConfigFactory,
  msalInterceptorConfigFactory,
  msalInitializerFactory,
} from './core/auth/msal.config';
import { mockApiInterceptor } from './core/mocks/mock-api.interceptor';
import { getMockAuthProviders } from './core/mocks/mock-auth';

function getRealAuthProviders(): Provider[] {
  return [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: MsalInterceptor,
      multi: true,
    },
    {
      provide: MSAL_INSTANCE,
      useFactory: msalInstanceFactory,
    },
    {
      provide: MSAL_GUARD_CONFIG,
      useFactory: msalGuardConfigFactory,
    },
    {
      provide: MSAL_INTERCEPTOR_CONFIG,
      useFactory: msalInterceptorConfigFactory,
    },
    {
      provide: APP_INITIALIZER,
      useFactory: msalInitializerFactory,
      deps: [MSAL_INSTANCE],
      multi: true,
    },
    MsalService,
    MsalGuard,
    MsalBroadcastService,
  ];
}

const useMocks = (environment as Record<string, unknown>)['useMocks'] === true;

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      ...(useMocks ? [withInterceptors([mockApiInterceptor])] : [withInterceptorsFromDi()])
    ),
    provideAnimationsAsync(),
    provideNativeDateAdapter(),
    ...(useMocks ? getMockAuthProviders() : getRealAuthProviders()),
  ],
};
