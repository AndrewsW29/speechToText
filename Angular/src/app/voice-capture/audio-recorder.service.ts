import { Injectable, signal } from '@angular/core';

const MIME = 'audio/webm;codecs=opus';
const BARS = 30;

@Injectable({ providedIn: 'root' })
export class AudioRecorderService {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];
  private audioCtx: AudioContext | null = null;
  private raf = 0;

  private readonly levelsState = signal<readonly number[]>([]);
  private readonly recordingState = signal(false);
  /** 0..1 amplitude per waveform bar, from an AnalyserNode. */
  readonly levels = this.levelsState.asReadonly();
  readonly recording = this.recordingState.asReadonly();

  async start(): Promise<void> {
    if (this.recorder) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      throw new Error('Microphone recording is not supported in this browser');
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      throw new Error('Microphone unavailable or permission denied');
    }
    const supported = MediaRecorder.isTypeSupported(MIME);
    this.chunks = [];
    const recorder = new MediaRecorder(this.stream, supported ? { mimeType: MIME } : undefined);
    recorder.ondataavailable = (e: BlobEvent): void => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };
    this.recorder = recorder;
    recorder.start();
    this.recordingState.set(true);
    this.startAnalyser(this.stream);
  }

  stop(): Promise<Blob> {
    const recorder = this.recorder;
    if (!recorder) return Promise.reject(new Error('Not recording'));
    return new Promise<Blob>((resolve) => {
      recorder.onstop = (): void => {
        const blob = new Blob(this.chunks, { type: recorder.mimeType || 'audio/webm' });
        this.release();
        resolve(blob);
      };
      recorder.stop();
    });
  }

  cancel(): void {
    if (this.recorder) {
      this.recorder.ondataavailable = null;
      this.recorder.onstop = null;
      if (this.recorder.state !== 'inactive') this.recorder.stop();
    }
    this.release();
  }

  private startAnalyser(stream: MediaStream): void {
    if (typeof AudioContext === 'undefined') return;
    this.audioCtx = new AudioContext();
    const analyser = this.audioCtx.createAnalyser();
    analyser.fftSize = 128;
    this.audioCtx.createMediaStreamSource(stream).connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = (): void => {
      analyser.getByteFrequencyData(data);
      const step = Math.max(1, Math.floor(data.length / BARS));
      this.levelsState.set(Array.from({ length: BARS }, (_, i) => (data[Math.min(i * step, data.length - 1)] ?? 0) / 255));
      this.raf = requestAnimationFrame(tick);
    };
    tick();
  }

  private release(): void {
    cancelAnimationFrame(this.raf);
    this.stream?.getTracks().forEach((t) => t.stop());
    void this.audioCtx?.close();
    this.audioCtx = null;
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
    this.levelsState.set([]);
    this.recordingState.set(false);
  }
}
