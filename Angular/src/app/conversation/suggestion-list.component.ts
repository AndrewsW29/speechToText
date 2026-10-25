import { ChangeDetectionStrategy, Component, output } from '@angular/core';
import { IconComponent } from '../shared/icon.component';

export const SUGGESTIONS: readonly string[] = [
  'Create a REST controller in Spring',
  'Explain dependency injection',
  'Write a JUnit test for a service',
  'How do I add validation to a DTO?',
];

@Component({
  selector: 'va-suggestion-list',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { display: flex; flex-direction: column; gap: 12px; }
    .label { font-weight: 700; color: var(--ink2); font-size: 14px; }
    .sug { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 56px; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--radius-card); background: var(--surface); text-align: left; font-size: 16px; line-height: 22px; }
    .sug:hover { border-color: var(--primary); }
    i { flex: none; width: 36px; height: 36px; border-radius: 999px; background: var(--tint); color: var(--link); display: flex; align-items: center; justify-content: center; }
  `,
  template: `<p class="label">Try asking</p>
    @for (s of suggestions; track s) {
      <button type="button" class="sug" (click)="chosen.emit(s)">
        <i><va-icon name="mic" [size]="20" /></i><span>“{{ s }}”</span>
      </button>
    }`,
})
export class SuggestionListComponent {
  protected readonly suggestions = SUGGESTIONS;
  readonly chosen = output<string>();
}
