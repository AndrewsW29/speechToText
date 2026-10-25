import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ConversationStore } from '../../conversation/conversation.store';
import { IconComponent, IconName } from '../../shared/icon.component';
import { ThemeService } from '../theme/theme.service';

interface NavItem {
  readonly label: string;
  readonly path: string;
  readonly icon: IconName;
}

@Component({
  selector: 'va-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    .app { display: flex; flex-wrap: wrap; min-height: 100vh; width: 100%; background: var(--bg); }
    .rail { flex: none; width: 80px; padding: 16px 8px; display: flex; flex-direction: column; align-items: center; gap: 8px; background: var(--surface); border-right: 1px solid var(--line); }
    .ri { display: flex; flex-direction: column; align-items: center; gap: 4px; width: 64px; min-height: var(--tap); padding: 10px 0; border: 0; border-radius: var(--radius-card); background: none; font-size: 12px; color: var(--ink2); text-decoration: none; }
    .ri.active { background: var(--tint); color: var(--link); font-weight: 700; }
    .theme { margin-top: auto; min-height: var(--tap); padding: 0 12px; border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); font-size: 12px; font-weight: 700; }
    .hist { flex: 0 1 300px; min-width: 260px; padding: 20px 12px; background: var(--surface); border-right: 1px solid var(--line); display: flex; flex-direction: column; gap: 8px; }
    .hist h2, .src h2 { margin: 0 8px 4px; font-size: 20px; font-weight: 800; }
    .hr { padding: 12px; border-radius: 8px; font-size: 14px; line-height: 20px; }
    .mn { flex: 999 1 520px; min-width: 0; display: flex; flex-direction: column; height: 100vh; }
    .src { flex: 1 1 260px; max-width: 320px; min-width: 240px; padding: 20px 16px; background: var(--surface); border-left: 1px solid var(--line); display: flex; flex-direction: column; gap: 12px; }
    .src a { display: flex; flex-direction: column; gap: 4px; padding: 14px; border: 1px solid var(--line); border-radius: var(--radius-card); text-decoration: none; min-height: var(--tap); }
    .src a b { color: var(--link); font-size: 15px; }
    .src a span { color: var(--muted); font-size: 13px; }
    @media (max-width: 1100px) { .hist, .src { display: none; } }
  `,
  template: `<div class="app">
    <nav class="rail" aria-label="Main">
      @for (item of nav; track item.path) {
        <a class="ri" [routerLink]="item.path" routerLinkActive="active" ariaCurrentWhenActive="page" [routerLinkActiveOptions]="{ exact: item.path === '/' }">
          <va-icon [name]="item.icon" /> {{ item.label }}
        </a>
      }
      <button type="button" class="theme" [attr.aria-pressed]="theme.theme() === 'dark'" (click)="theme.toggle()">
        {{ theme.theme() === 'dark' ? 'Light' : 'Dark' }}
      </button>
    </nav>
    <aside class="hist" aria-label="History">
      <h2>History</h2>
      @for (h of store.history(); track h.id) {
        <div class="hr">{{ h.question }}</div>
      } @empty {
        <p class="muted" style="padding: 0 8px">No questions yet.</p>
      }
    </aside>
    <main class="mn"><router-outlet /></main>
    <aside class="src" aria-label="Sources">
      <h2>Sources</h2>
      @for (s of store.sources(); track s.id) {
        @if (s.url) {
          <a [href]="s.url" target="_blank" rel="noopener noreferrer"><b>{{ s.title }}</b></a>
        } @else {
          <a><b>{{ s.title }}</b></a>
        }
      } @empty {
        <p class="muted" style="padding: 0 4px">Sources appear with each answer.</p>
      }
    </aside>
  </div>`,
})
export class ShellComponent {
  protected readonly store = inject(ConversationStore);
  protected readonly theme = inject(ThemeService);
  protected readonly nav: readonly NavItem[] = [
    { label: 'Ask', path: '/', icon: 'mic' },
    { label: 'History', path: '/history', icon: 'history' },
    { label: 'Saved', path: '/saved', icon: 'saved' },
    { label: 'Settings', path: '/settings', icon: 'settings' },
  ];
}
