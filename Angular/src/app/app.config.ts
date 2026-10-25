import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { AuthTokenProvider, StubAuthTokenProvider } from './core/api/auth-token.provider';
import { authInterceptor } from './core/api/auth.interceptor';

// Composition root: wires adapters to their abstractions.
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    { provide: AuthTokenProvider, useClass: StubAuthTokenProvider },
  ],
};
