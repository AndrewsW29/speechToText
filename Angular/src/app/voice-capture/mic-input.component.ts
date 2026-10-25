import { ChangeDetectionStrategy, Component, model, output } from '@angular/core';
import { IconComponent } from '../shared/icon.component';

@Component({
  selector: 'va-mic-input',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { display: block; width: 100%; max-width: 760px; margin: 0 auto; }
    .inp { display: flex; align-items: center; gap: 12px; padding: 12px 32px 4px; }
    input { flex: 1; min-width: 0; height: 56px; border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--field); padding: 0 20px; font: inherit; font-size: 16px; color: var(--ink); }
    .mic { flex: none; width: 56px; height: 56px; border: 0; border-radius: 999px; background: var(--primary); color: var(--on-primary); display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow); }
  `,
  template: `<div class="inp">
    <input
      type="text"
      aria-label="Type a question"
      placeholder="Type a question…"
      [value]="text()"
      (input)="text.set($any($event.target).value)"
      (keydown.enter)="submit()"
    />
    <button type="button" class="mic" aria-label="Start listening, shortcut Control Shift M" (click)="micPressed.emit()">
      <va-icon name="mic" [size]="26" />
    </button>
  </div>`,
})
export class MicInputComponent {
  readonly text = model('');
  readonly micPressed = output<void>();
  readonly submitted = output<string>();

  protected submit(): void {
    const value = this.text().trim();
    if (value) this.submitted.emit(value);
  }
}
