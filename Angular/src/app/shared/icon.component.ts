import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export type IconName = 'mic' | 'history' | 'saved' | 'settings' | 'copy' | 'close' | 'edit' | 'check' | 'stop';

const PATHS: Record<IconName, string> = {
  mic: 'M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z M5 11a7 7 0 0 0 14 0M12 18v3',
  history: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 7v5l3 2',
  saved: 'M6 3h12v18l-6-4-6 4z',
  settings: 'M4 7h9M17 7h3M4 17h3M11 17h9 M15 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4z M9 15a2 2 0 1 0 0 4 2 2 0 0 0 0-4z',
  copy: 'M11 9h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-7a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z M5 15V5a2 2 0 0 1 2-2h8',
  close: 'M6 6l12 12M18 6L6 18',
  edit: 'M4 20h4L19 9l-4-4L4 16z',
  check: 'M5 12l5 5L20 7',
  stop: 'M8 5h8a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3z',
};

@Component({
  selector: 'va-icon',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'display:inline-flex' },
  template: `<svg
    [attr.width]="size()"
    [attr.height]="size()"
    viewBox="0 0 24 24"
    [attr.fill]="name() === 'stop' ? 'currentColor' : 'none'"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path [attr.d]="path()" />
  </svg>`,
})
export class IconComponent {
  readonly name = input.required<IconName>();
  readonly size = input(24);
  protected readonly path = computed(() => PATHS[this.name()]);
}
