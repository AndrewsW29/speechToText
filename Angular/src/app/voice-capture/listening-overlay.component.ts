import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import { IconComponent } from '../shared/icon.component';

const RING = 182;

@Component({
  selector: 'va-listening-overlay',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { display: block; width: 100%; max-width: 760px; margin: 0 auto; padding: 0 32px; }
    .ovc { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 20px; border-radius: var(--radius-card); background: var(--surface); border: 1px solid var(--line); box-shadow: var(--shadow); }
    .status { display: flex; align-items: center; gap: 8px; font-size: 20px; font-weight: 700; }
    .status i { width: 10px; height: 10px; border-radius: 999px; background: var(--ac); }
    .wave { display: flex; align-items: center; justify-content: center; gap: 4px; height: 72px; }
    .wave b { width: 5px; border-radius: 3px; background: var(--ac); animation: w 1s ease-in-out infinite alternate; transform-origin: center; transition: height 0.08s; }
    .wave.reduced b { animation: none; }
    @keyframes w { from { transform: scaleY(0.45); } to { transform: scaleY(1); } }
    @media (prefers-reduced-motion: reduce) { .wave b { animation: none; } }
    .heard { align-self: stretch; padding: 16px; border-radius: var(--radius-card); background: var(--bg); min-height: 92px; }
    .heard small { display: block; font-size: 12px; font-weight: 700; color: var(--muted); margin-bottom: 4px; }
    .heard p { font-size: 17px; line-height: 26px; font-style: italic; color: var(--ink2); }
    .lact { align-self: stretch; display: flex; align-items: center; justify-content: space-between; }
    .btn { min-height: 48px; padding: 0 24px; border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); font-size: 16px; font-weight: 700; }
    .right { display: flex; align-items: center; gap: 12px; }
    .ring { position: relative; width: 64px; height: 64px; padding: 0; border: 0; background: none; display: flex; align-items: center; justify-content: center; }
    .ring svg.r { position: absolute; inset: 0; }
    .ring span { width: 44px; height: 44px; border-radius: 999px; background: var(--primary); color: var(--on-primary); display: flex; align-items: center; justify-content: center; }
  `,
  template: `<section class="ovc" aria-label="Listening">
    <div class="status" role="status"><i></i>Listening…</div>
    <div class="wave" [class.reduced]="reduced" aria-hidden="true">
      @for (l of levels(); track $index) {
        <b [style.height.px]="barHeight(l)" [style.animation-delay.s]="($index % 7) * 0.11"></b>
      }
    </div>
    @if (heard()) {
      <div class="heard"><small>I heard</small><p>“{{ heard() }}”</p></div>
    }
    <div class="lact">
      <button type="button" class="btn" (click)="cancelled.emit()">Cancel</button>
      <span class="right">
        <span class="muted">Auto-stop in {{ secondsLeft() }} s</span>
        <button type="button" class="ring" aria-label="Done, stop listening" (click)="done.emit()">
          <svg class="r" width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
            <circle cx="32" cy="32" r="29" stroke="var(--track)" stroke-width="4" />
            <circle cx="32" cy="32" r="29" stroke="var(--ac)" stroke-width="4" stroke-linecap="round" [attr.stroke-dasharray]="ringLength" [attr.stroke-dashoffset]="offset()" transform="rotate(-90 32 32)" />
          </svg>
          <span><va-icon name="stop" [size]="18" /></span>
        </button>
      </span>
    </div>
  </section>`,
})
export class ListeningOverlayComponent {
  readonly levels = input<readonly number[]>([]);
  readonly secondsLeft = input.required<number>();
  readonly totalSeconds = input.required<number>();
  readonly heard = input('');
  readonly cancelled = output<void>();
  readonly done = output<void>();

  protected readonly ringLength = RING;
  protected readonly reduced = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  protected readonly offset = computed(() => {
    const total = this.totalSeconds();
    return total > 0 ? RING * (1 - Math.min(1, Math.max(0, this.secondsLeft() / total))) : RING;
  });

  protected barHeight(level: number): number {
    return 8 + Math.round(Math.min(1, Math.max(0, level)) * 56);
  }
}
