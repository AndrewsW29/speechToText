import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { IconComponent } from '../shared/icon.component';

@Component({
  selector: 'va-user-bubble',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { align-self: flex-end; max-width: 520px; display: flex; gap: 8px; align-items: flex-start; padding: 12px 16px; border-radius: 20px 20px 4px 20px; background: var(--primary); color: var(--on-primary); font-size: 16px; line-height: 24px; }
    button { flex: none; width: 28px; height: 28px; border: 0; border-radius: 999px; background: rgba(255, 255, 255, 0.2); color: #fff; display: flex; align-items: center; justify-content: center; }
  `,
  template: `<span>{{ text() }}</span>
    <button type="button" aria-label="Edit question" (click)="edit.emit()"><va-icon name="edit" [size]="14" /></button>`,
})
export class UserBubbleComponent {
  readonly text = input.required<string>();
  readonly edit = output<void>();
}
