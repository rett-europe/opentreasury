import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Route guard that blocks Viewer role from admin-only pages */
export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    authService.login();
    return false;
  }

  if (authService.isAdmin()) {
    return true;
  }

  // Viewers get redirected to dashboard
  return router.createUrlTree(['/dashboard']);
};
