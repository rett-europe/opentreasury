import { Routes } from '@angular/router';
import { MsalGuard } from '@azure/msal-angular';
import { adminGuard } from './core/auth/admin.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then(
        (m) => m.DashboardComponent,
      ),
    canActivate: [MsalGuard],
  },
  {
    path: 'transactions',
    loadComponent: () =>
      import('./features/transactions/transaction-list.component').then(
        (m) => m.TransactionListComponent,
      ),
    canActivate: [MsalGuard],
  },
  {
    path: 'transactions/new',
    loadComponent: () =>
      import('./features/transactions/transaction-form.component').then(
        (m) => m.TransactionFormComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: 'transactions/:id/edit',
    loadComponent: () =>
      import('./features/transactions/transaction-form.component').then(
        (m) => m.TransactionFormComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: 'categories',
    loadComponent: () =>
      import('./features/categories/category-list.component').then(
        (m) => m.CategoryListComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: 'tags',
    loadComponent: () =>
      import('./features/tags/tag-list.component').then(
        (m) => m.TagListComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: 'accounts',
    loadComponent: () =>
      import('./features/accounts/account-list.component').then(
        (m) => m.AccountListComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: 'export',
    loadComponent: () =>
      import('./features/export/export.component').then(
        (m) => m.ExportComponent,
      ),
    canActivate: [MsalGuard],
  },
  {
    path: 'import',
    loadComponent: () =>
      import('./features/import/import.component').then(
        (m) => m.ImportComponent,
      ),
    canActivate: [MsalGuard, adminGuard],
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
