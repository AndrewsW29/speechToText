import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    title: 'Ask',
    loadComponent: () => import('./conversation/conversation.component').then((m) => m.ConversationComponent),
  },
  ...(['history', 'saved', 'settings'] as const).map((path) => ({
    path,
    title: path.charAt(0).toUpperCase() + path.slice(1),
    loadComponent: () => import('./core/shell/section-placeholder.component').then((m) => m.SectionPlaceholderComponent),
  })),
  { path: '**', redirectTo: '' },
];
