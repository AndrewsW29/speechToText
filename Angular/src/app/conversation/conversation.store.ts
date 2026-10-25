import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiProblemError, QuestionResponse } from '../core/api/api.models';
import { QuestionsApi } from '../core/api/questions-api.service';

export type ConversationView = 'idle' | 'listening' | 'answer';

export interface HistoryEntry {
  readonly id: string;
  readonly question: string;
}

@Injectable({ providedIn: 'root' })
export class ConversationStore {
  private readonly api = inject(QuestionsApi);

  readonly view = signal<ConversationView>('idle');
  readonly context = signal<string | null>('Spring · Java');
  readonly draft = signal('');
  readonly question = signal('');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly response = signal<QuestionResponse | null>(null);
  readonly history = signal<readonly HistoryEntry[]>([]);

  readonly answerText = computed(() => this.response()?.answer?.text ?? '');
  readonly sources = computed(() => this.response()?.answer?.sources ?? []);
  readonly clarification = computed(() => this.response()?.clarification ?? null);
  /** Refusals and app commands carry a plain message instead of an answer. */
  readonly notice = computed(() => {
    const r = this.response();
    return r && r.status !== 'answer' && !r.clarification ? r.message : null;
  });

  setListening(on: boolean): void {
    if (on) this.view.set('listening');
    else if (this.view() === 'listening') this.view.set(this.question() ? 'answer' : 'idle');
  }

  clearContext(): void {
    this.context.set(null);
  }

  submitAudio(audio: Blob): void {
    this.begin('Transcribing…');
    this.api.ask(audio).subscribe({
      next: (r) => {
        this.question.set(r.transcript.text);
        this.response.set(r);
        this.loading.set(false);
        this.history.update((h) => [{ id: r.question_id, question: r.transcript.text }, ...h]);
      },
      error: (e: unknown) => {
        this.loading.set(false);
        this.error.set(e instanceof ApiProblemError ? e.message : 'Something went wrong. Try again.');
      },
    });
  }

  /** The /v1/questions contract accepts audio only, so typed questions cannot be answered yet. */
  askText(text: string): void {
    this.begin(text);
    this.question.set(text);
    this.loading.set(false);
    this.error.set('Typed questions are not supported by the API yet. Please use the microphone.');
  }

  /** Picking a clarification option narrows the context; the user then repeats the question. */
  pickOption(option: string): void {
    this.context.set(option);
    this.error.set(`Using ${option}. Tap the microphone and ask again.`);
    this.response.set(null);
  }

  edit(): void {
    this.draft.set(this.question());
    this.view.set('idle');
    this.response.set(null);
    this.error.set(null);
  }

  private begin(label: string): void {
    this.view.set('answer');
    this.question.set(label);
    this.response.set(null);
    this.error.set(null);
    this.loading.set(true);
  }
}
