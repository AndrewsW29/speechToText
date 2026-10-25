import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AudioRecorderService } from './audio-recorder.service';

class FakeMediaRecorder {
  static instances: FakeMediaRecorder[] = [];
  static isTypeSupported = vi.fn(() => true);
  state: 'inactive' | 'recording' = 'inactive';
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  constructor(
    readonly stream: MediaStream,
    readonly options?: MediaRecorderOptions,
  ) {
    FakeMediaRecorder.instances.push(this);
  }
  start(): void {
    this.state = 'recording';
  }
  stop(): void {
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['abc'], { type: 'audio/webm' }) });
    this.onstop?.();
  }
}

describe('AudioRecorderService', () => {
  const trackStop = vi.fn();
  let getUserMedia: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    FakeMediaRecorder.instances = [];
    trackStop.mockClear();
    getUserMedia = vi.fn(async () => ({ getTracks: () => [{ stop: trackStop }] }) as unknown as MediaStream);
    vi.stubGlobal('MediaRecorder', FakeMediaRecorder);
    vi.stubGlobal('AudioContext', undefined);
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia } });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('requests the microphone and records WebM/Opus', async () => {
    const svc = TestBed.inject(AudioRecorderService);
    await svc.start();
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(FakeMediaRecorder.instances[0]?.options?.mimeType).toBe('audio/webm;codecs=opus');
    expect(svc.recording()).toBe(true);
  });

  it('stop() resolves with the recorded blob and releases the mic', async () => {
    const svc = TestBed.inject(AudioRecorderService);
    await svc.start();
    const blob = await svc.stop();
    expect(blob.size).toBe(3);
    expect(blob.type).toContain('audio/webm');
    expect(trackStop).toHaveBeenCalled();
    expect(svc.recording()).toBe(false);
  });

  it('cancel() releases the mic without producing audio', async () => {
    const svc = TestBed.inject(AudioRecorderService);
    await svc.start();
    svc.cancel();
    expect(trackStop).toHaveBeenCalled();
    expect(svc.recording()).toBe(false);
  });

  it('rejects when microphone access is denied', async () => {
    getUserMedia.mockRejectedValueOnce(new DOMException('denied', 'NotAllowedError'));
    const svc = TestBed.inject(AudioRecorderService);
    await expect(svc.start()).rejects.toThrow(/microphone/i);
    expect(svc.recording()).toBe(false);
  });

  it('rejects stop() when not recording', async () => {
    await expect(TestBed.inject(AudioRecorderService).stop()).rejects.toThrow(/not recording/i);
  });
});
