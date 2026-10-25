import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { VoiceCaptureComponent } from '../voice-capture/voice-capture.component';
import { AnswerCardComponent } from './answer-card.component';
import { ContextChipComponent } from './context-chip.component';
import { ConversationStore } from './conversation.store';
import { SourcesPanelComponent } from './sources-panel.component';
import { SuggestionListComponent } from './suggestion-list.component';
import { UserBubbleComponent } from './user-bubble.component';

@Component({
  selector: 'va-conversation',
  imports: [VoiceCaptureComponent, AnswerCardComponent, ContextChipComponent, SuggestionListComponent, UserBubbleComponent, SourcesPanelComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { display: flex; flex-direction: column; flex: 1; min-height: 0; }
    .body { display: flex; flex: 1; min-height: 0; }
    .col { display: flex; flex-direction: column; flex: 1; min-width: 0; min-height: 0; }
    va-sources-panel { flex: 0 1 320px; min-width: 240px; display: flex; }
    va-sources-panel > aside { flex: 1; overflow-y: auto; }
    @media (max-width: 1100px) { va-sources-panel { display: none; } }
    .mh { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 32px; background: var(--surface); border-bottom: 1px solid var(--line); }
    h1 { font-size: 24px; line-height: 32px; font-weight: 800; }
    .main { flex: 1; min-height: 0; overflow-y: auto; width: 100%; max-width: 760px; margin: 0 auto; padding: 24px 32px; display: flex; flex-direction: column; gap: 12px; }
    .follow { display: flex; gap: 8px; flex-wrap: wrap; }
    .chip { display: inline-flex; align-items: center; min-height: var(--tap); padding: 0 14px; border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); font-size: 14px; }
    .err { padding: 16px; border-radius: var(--radius-card); border: 1px solid var(--line); background: var(--surface); }
    .idle-chip { align-self: flex-start; }
  `,
  template: `
    <div class="mh">
      <h1>{{ store.view() === 'answer' ? store.question() : 'Ask' }}</h1>
      @if (store.context(); as ctx) {
        <va-context-chip [context]="ctx" (cleared)="store.clearContext()" />
      }
    </div>
    <div class="body"><div class="col"><div class="main" aria-live="polite">
      @if (store.view() === 'answer') {
        <va-user-bubble [text]="store.question()" (edit)="store.edit()" />
        @if (store.loading()) {
          <p class="muted" role="status">Working on it…</p>
        }
        @if (store.error(); as message) {
          <p class="err" role="alert">{{ message }}</p>
        }
        @if (store.clarification(); as c) {
          <section class="err" role="group" aria-label="Clarification">
            <p>{{ c.question }}</p>
            <div class="follow">
              @for (option of c.options; track option) {
                <button type="button" class="chip" (click)="store.pickOption(option)">{{ option }}</button>
              }
            </div>
          </section>
        }
        @if (store.notice(); as note) {
          <p class="err" role="status">{{ note }}</p>
        }
        @if (store.response(); as r) {
          @if (r.answer; as a) {
            <va-answer-card [text]="a.text" [sources]="a.sources" />
            <div class="follow">
              <button type="button" class="chip" (click)="store.askText('Add validation')">Add validation</button>
              <button type="button" class="chip" (click)="store.askText('Write a test')">Write a test</button>
            </div>
          }
        }
      } @else {
        <va-suggestion-list (chosen)="store.askText($event)" />
        <p class="muted">Tap the mic and speak, or type your question. Answers include code and sources.</p>
      }
    </div>
    <va-voice-capture
      [(text)]="store.draft"
      (audioCaptured)="store.submitAudio($event)"
      (textSubmitted)="store.askText($event)"
      (listeningChange)="store.setListening($event)"
    />
    </div>
    @if (store.response(); as r) {
      <va-sources-panel [sources]="r.answer.sources" />
    }
    </div>
  `,
})
export class ConversationComponent {
  protected readonly store = inject(ConversationStore);
}
