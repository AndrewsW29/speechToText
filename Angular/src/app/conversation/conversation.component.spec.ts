import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QuestionResponse } from '../core/api/api.models';
import { QuestionsApi } from '../core/api/questions-api.service';
import { AudioRecorderService } from '../voice-capture/audio-recorder.service';
import { ConversationComponent } from './conversation.component';
import { ConversationStore } from './conversation.store';

const RESPONSE: QuestionResponse = {
  status: 'answer',
  question_id: 'q1',
  transcript: { text: 'Create a controller', language: 'en' },
  answer: {
    text: 'Step one.\n```java\n@RestController\nclass A {}\n```\nDone.',
    sources: [{ id: 's1', title: 'Spring Docs', url: 'https://spring.io', kind: 'documentation' }],
  },
  clarification: null,
  message: null,
  intent: null,
};

describe('ConversationComponent', () => {
  let fixture: ComponentFixture<ConversationComponent>;
  let store: ConversationStore;
  const writeText = vi.fn(async () => undefined);
  const el = (): HTMLElement => fixture.nativeElement as HTMLElement;

  beforeEach(async () => {
    writeText.mockClear();
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: QuestionsApi, useValue: { ask: vi.fn(() => of(RESPONSE)) } },
        {
          provide: AudioRecorderService,
          useValue: { levels: signal([]), recording: signal(false), start: vi.fn(), stop: vi.fn(), cancel: vi.fn() },
        },
      ],
    });
    store = TestBed.inject(ConversationStore);
    fixture = TestBed.createComponent(ConversationComponent);
    await fixture.whenStable();
  });
  afterEach(() => vi.restoreAllMocks());

  it('shows four suggestions under "Try asking" in the idle view', () => {
    expect(el().textContent).toContain('Try asking');
    expect(el().querySelectorAll('va-suggestion-list .sug').length).toBe(4);
  });

  it('starts a question when a suggestion is chosen', async () => {
    (el().querySelector('va-suggestion-list .sug') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(store.view()).toBe('answer');
    expect(store.question()).toBe('Create a REST controller in Spring');
    expect(el().querySelector('va-user-bubble')?.textContent).toContain('Create a REST controller in Spring');
  });

  it('clears the context chip with an accessible label', async () => {
    const chip = el().querySelector('va-context-chip button') as HTMLButtonElement;
    expect(chip.getAttribute('aria-label')).toBe('Clear context: Spring, Java');
    chip.click();
    await fixture.whenStable();
    expect(store.context()).toBeNull();
    expect(el().querySelector('va-context-chip')).toBeNull();
  });

  describe('with an answer', () => {
    beforeEach(async () => {
      store.submitAudio(new Blob(['a']));
      await fixture.whenStable();
    });

    it('renders transcript, code block and sources', () => {
      expect(el().querySelector('va-user-bubble')?.textContent).toContain('Create a controller');
      expect(el().querySelector('va-code-block pre')?.textContent).toContain('@RestController');
      expect(el().querySelector('va-code-block')?.textContent).toContain('java');
    });

    it('Copy writes the code to the clipboard and confirms', async () => {
      (el().querySelector('va-code-block button[aria-label="Copy code"]') as HTMLButtonElement).click();
      await fixture.whenStable();
      expect(writeText).toHaveBeenCalledWith('@RestController\nclass A {}');
      expect(el().querySelector('va-code-block button')?.textContent).toContain('Copied');
    });

    it('Edit question re-opens the input with the transcript', async () => {
      (el().querySelector('va-user-bubble button[aria-label="Edit question"]') as HTMLButtonElement).click();
      await fixture.whenStable();
      expect(store.view()).toBe('idle');
      expect((el().querySelector('input') as HTMLInputElement).value).toBe('Create a controller');
    });
  });
});
