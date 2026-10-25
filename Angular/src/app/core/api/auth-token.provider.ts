import { Injectable } from '@angular/core';

/** Port: where the bearer JWT comes from (Keycloak adapter replaces the stub later). */
export abstract class AuthTokenProvider {
  abstract getToken(): string | null;
}

@Injectable()
export class StubAuthTokenProvider extends AuthTokenProvider {
  getToken(): string | null {
    return null;
  }
}
