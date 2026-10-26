import { Routes } from '@angular/router';

import { authGuard } from './core/auth.service';

export const routes: Routes = [
  {
    path: 'login',
    title: 'Connexion · Console OpsReady',
    loadComponent: () => import('./features/login/login').then((m) => m.LoginPage),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/shell').then((m) => m.Shell),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'agents' },
      {
        path: 'agents',
        title: 'Agents · Console OpsReady',
        loadComponent: () => import('./features/agents/agents-list').then((m) => m.AgentsListPage),
      },
      {
        path: 'alerts',
        title: 'Alertes · Console OpsReady',
        loadComponent: () => import('./features/alerts/alerts').then((m) => m.AlertsPage),
      },
    ],
  },
  { path: '**', redirectTo: 'agents' },
];
