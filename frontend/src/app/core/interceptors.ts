import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { EMPTY, catchError, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { NotificationService } from './notification.service';

/** Adds the JWT token to /api calls and lets everything else through. */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(AuthService).token();
  if (!token || !request.url.startsWith('/api/')) {
    return next(request);
  }
  return next(request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};

/**
 * Translates HTTP errors: 401 outside login => logout, 5xx and network
 * failures => global notification. Business errors (4xx) stay handled by
 * each page (inline messages).
 */
export const errorInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const notify = inject(NotificationService);

  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !request.url.includes('/auth/login')) {
        auth.logout();
        return EMPTY;
      }
      if (error.status >= 500 || error.status === 0) {
        notify.error(apiErrorMessage(error));
      }
      return throwError(() => error);
    }),
  );
};

export function apiErrorMessage(error: HttpErrorResponse): string {
  const body = error.error as { error?: { message?: string } } | null;
  return body?.error?.message ?? 'Service indisponible, réessayez plus tard';
}
