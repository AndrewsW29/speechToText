import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthTokenProvider } from './auth-token.provider';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthTokenProvider).getToken();
  return next(token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req);
};
