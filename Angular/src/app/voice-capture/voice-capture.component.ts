import { ChangeDetectionStrategy, Component, DestroyRef, inject, model, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ShortcutsService } from '../core/shortcuts/shortcuts.service';
import { AudioRecorderService } from './audio-recorder.service';
import { ListeningOverlayComponent } from './listening-overlay.component';
import { MicInputComponent } from './mic-input.component';

const MAX_SECONDS = 30;

@Component({
  selector: 'va-voice-capture',
  imports: [ListeningOverlayComponent, MicInputComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    .err { max-width: 760px; margin: 0 auto; padding: 0 32px; color: var(--ink); font-size: 14px; }
    .hint { width: 100%; max-width: 760px; margin: 0 auto; padding: 0 32px 20px; text-align: right; }
  `,
  template: `
    @if (listening()) {
      <va-listening-overlay
        [levels]="recorder.levels()"
        [secondsLeft]="secondsLeft()"
        [totalSeconds]="maxSeconds"
        (cancelled)="cancel()"
        (done)="finish()"
      />
    }
    @if (error(); as message) {
      <p class="err" role="alert">{{ message }}</p>
    }
    <va-mic-input [(text)]="text" (micPressed)="start()" (submitted)="textSubmitted.emit($event)" />
    <p class="hint muted">Press <kbd>Ctrl</kbd> <kbd>Shift</kbd> <kbd>M</kbd> to speak, <kbd>Esc</kbd> to cancel</p>
  `,
})
export class VoiceCaptureComponent {
  protected readonly recorder = inject(AudioRecorderService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly maxSeconds = MAX_SECONDS;

  readonly text = model('');
  readonly audioCaptured = output<Blob>();
  readonly textSubmitted = output<string>();
  readonly listeningChange = output<boolean>();

  protected readonly listening = signal(false);
  protected readonly secondsLeft = signal(MAX_SECONDS);
  protected readonly error = signal<string | null>(null);
  private timer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    const shortcuts = inject(ShortcutsService);
    shortcuts.start$.pipe(takeUntilDestroyed()).subscribe(() => void this.start());
    shortcuts.cancel$.pipe(takeUntilDestroyed()).subscribe(() => this.cancel());
    this.destroyRef.onDestroy(() => {
      this.clearTimer();
      if (this.listening()) this.recorder.cancel();
    });
  }

  protected async start(): Promise<void> {
    if (this.listening()) return;
    this.error.set(null);
    try {
      await this.recorder.start();
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'Could not start recording');
      return;
    }
    this.secondsLeft.set(MAX_SECONDS);
    this.setListening(true);
    this.timer = setInterval(() => {
      const next = this.secondsLeft() - 1;
      this.secondsLeft.set(Math.max(0, next));
      if (next <= 0) void this.finish();
    }, 1000);
  }

  protected cancel(): void {
    if (!this.listening()) return;
    this.clearTimer();
    this.recorder.cancel();
    this.setListening(false);
  }

  protected async finish(): Promise<void> {
    if (!this.listening()) return;
    this.clearTimer();
    this.setListening(false);
    try {
      this.audioCaptured.emit(await this.recorder.stop());
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'Recording failed');
    }
  }

  private setListening(value: boolean): void {
    this.listening.set(value);
    this.listeningChange.emit(value);
  }

  private clearTimer(): void {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
  }
}
