import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AudioRecorderService } from './audio-recorder.service';
import { VoiceCaptureComponent } from './voice-capture.component';
import { signal } from '@angular/core';

describe('VoiceCaptureComponent', () => {
  let fixture: ComponentFixture<VoiceCaptureComponent>;
  const blob = new Blob(['audio'], { type: 'audio/webm' });
  const recorder = {
    levels: signal<readonly number[]>([0.2, 0.4]),
    recording: signal(false),
    start: vi.fn(async () => undefined),
    stop: vi.fn(async () => blob),
    cancel: vi.fn(),
  };
  const el = (): HTMLElement => fixture.nativeElement as HTMLElement;
  const click = (sel: string): void => (el().querySelector(sel) as HTMLButtonElement).click();

  beforeEach(async () => {
    vi.clearAllMocks();
    TestBed.configureTestingModule({ providers: [{ provide: AudioRecorderService, useValue: recorder }] });
    fixture = TestBed.createComponent(VoiceCaptureComponent);
    await fixture.whenStable();
  });

  it('starts recording and shows the overlay when the mic is pressed', async () => {
    click('button.mic');
    await fixture.whenStable();
    expect(recorder.start).toHaveBeenCalled();
    expect(el().querySelector('[role="status"]')?.textContent).toContain('Listening');
  });

  it('Done stops and emits the captured audio', async () => {
    const captured = vi.fn();
    fixture.componentInstance.audioCaptured.subscribe(captured);
    click('button.mic');
    await fixture.whenStable();
    click('button[aria-label="Done, stop listening"]');
    await fixture.whenStable();
    expect(recorder.stop).toHaveBeenCalled();
    expect(captured).toHaveBeenCalledWith(blob);
    expect(el().querySelector('[role="status"]')).toBeNull();
  });

  it('Cancel discards the recording without emitting', async () => {
    const captured = vi.fn();
    fixture.componentInstance.audioCaptured.subscribe(captured);
    click('button.mic');
    await fixture.whenStable();
    click('button.btn');
    await fixture.whenStable();
    expect(recorder.cancel).toHaveBeenCalled();
    expect(captured).not.toHaveBeenCalled();
    expect(el().querySelector('[role="status"]')).toBeNull();
  });

  it('Ctrl+Shift+M starts and Escape cancels', async () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'M', code: 'KeyM', ctrlKey: true, shiftKey: true }));
    await fixture.whenStable();
    expect(recorder.start).toHaveBeenCalled();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape' }));
    await fixture.whenStable();
    expect(recorder.cancel).toHaveBeenCalled();
  });

  it('emits the typed question on Enter', async () => {
    const submitted = vi.fn();
    fixture.componentInstance.textSubmitted.subscribe(submitted);
    const input = el().querySelector('input') as HTMLInputElement;
    input.value = 'What is DI?';
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    await fixture.whenStable();
    expect(submitted).toHaveBeenCalledWith('What is DI?');
  });

  it('reports a recorder failure instead of listening', async () => {
    recorder.start.mockRejectedValueOnce(new Error('Microphone unavailable'));
    click('button.mic');
    await fixture.whenStable();
    expect(el().querySelector('[role="alert"]')?.textContent).toContain('Microphone unavailable');
    expect(el().querySelector('[role="status"]')).toBeNull();
  });
});
