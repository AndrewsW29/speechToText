import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QuestionResponse } from '../core/api/api.models';
import { QuestionsApi } from '../core/api/questions-api.service';
import { AudioRecorderService } from '../voice-capture/audio-recorder.service';
import { ConversationComponent } from './conversation.component';
import { ConversationStore } from './conversation.store';

const BASE: QuestionResponse = {
  status: 'answer',
  question_id: 'q1',
  transcript: { text: 'create a controller', language: 'en' },
  answer: null,
  clarification: null,
  message: null,
  intent: null,
};

describe('ConversationComponent response statuses', () => {
  let fixture: ComponentFixture<ConversationComponent>;
  let store: ConversationStore;
  const el = (): HTMLElement => fixture.nativeElement as HTMLElement;

  const show = (response: QuestionResponse): void => {
    store.view.set('answer');
    store.question.set(response.transcript.text);
    store.response.set(response);
    fixture.detectChanges();
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: QuestionsApi, useValue: { ask: vi.fn(() => of(BASE)) } },
        {
          provide: AudioRecorderService,
          useValue: { levels: signal([]), recording: signal(false), start: vi.fn(), stop: vi.fn(), cancel: vi.fn() },
        },
      ],
    });
    store = TestBed.inject(ConversationStore);
    fixture = TestBed.createComponent(ConversationComponent);
    fixture.detectChanges();
  });

  it('shows the clarifying question with one chip per option', () => {
    show({
      ...BASE,
      status: 'clarify',
      clarification: { question: 'Which language should I use?', options: ['java', 'kotlin', 'typescript'] },
    });
    const group = el().querySelector('[aria-label="Clarification"]')!;
    expect(group.textContent).toContain('Which language should I use?');
    expect(group.querySelectorAll('button')).toHaveLength(3);
    expect(el().querySelector('va-answer-card')).toBeNull();
  });

  it('picking an option sets the context and asks the user to repeat the question', () => {
    show({ ...BASE, status: 'clarify', clarification: { question: 'Which language?', options: ['kotlin'] } });
    (el().querySelector('[aria-label="Clarification"] button') as HTMLButtonElement).click();
    expect(store.context()).toBe('kotlin');
    expect(store.error()).toContain('ask again');
  });

  it('shows the refusal message for abstain responses without an answer card', () => {
    show({ ...BASE, status: 'abstain', message: "That's outside what I can help with." });
    expect(el().textContent).toContain("That's outside what I can help with.");
    expect(el().querySelector('va-answer-card')).toBeNull();
  });

  it('exposes no notice for normal answers', () => {
    show({ ...BASE, answer: { text: 'hi', sources: [] } });
    expect(store.notice()).toBeNull();
    expect(el().querySelector('va-answer-card')).not.toBeNull();
  });
});
