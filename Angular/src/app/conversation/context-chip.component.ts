import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { IconComponent } from '../shared/icon.component';

@Component({
  selector: 'va-context-chip',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    button { display: inline-flex; align-items: center; gap: 6px; min-height: var(--tap); padding: 0 10px 0 14px; border: 0; border-radius: var(--radius-pill); background: var(--tint); color: var(--link); font-size: 14px; font-weight: 700; }
  `,
  template: `<button type="button" [attr.aria-label]="label()" (click)="cleared.emit()">
    {{ context() }}<va-icon name="close" [size]="16" />
  </button>`,
})
export class ContextChipComponent {
  readonly context = input.required<string>();
  readonly cleared = output<void>();
  protected readonly label = computed(() => `Clear context: ${this.context().replaceAll(' · ', ', ')}`);
}
