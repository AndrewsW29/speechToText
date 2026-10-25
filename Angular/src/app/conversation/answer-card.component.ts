import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Source } from '../core/api/api.models';
import { CodeBlockComponent } from '../shared/code-block.component';

export type AnswerSegment =
  | { readonly kind: 'text'; readonly text: string }
  | { readonly kind: 'code'; readonly language: string; readonly code: string };

/** Splits an answer into prose paragraphs and fenced code blocks. */
export function parseAnswer(text: string): AnswerSegment[] {
  const out: AnswerSegment[] = [];
  const re = /```([\w+#-]*)\n([\s\S]*?)```/g;
  let last = 0;
  const pushText = (chunk: string): void => {
    for (const p of chunk.split(/\n{2,}|\n/)) if (p.trim()) out.push({ kind: 'text', text: p.trim() });
  };
  for (const m of text.matchAll(re)) {
    pushText(text.slice(last, m.index));
    out.push({ kind: 'code', language: m[1] || 'text', code: (m[2] ?? '').replace(/\n+$/, '') });
    last = (m.index ?? 0) + m[0].length;
  }
  pushText(text.slice(last));
  return out;
}

@Component({
  selector: 'va-answer-card',
  imports: [CodeBlockComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    article { display: flex; flex-direction: column; gap: 12px; padding: 16px; border-radius: var(--radius-card); background: var(--surface); border: 1px solid var(--line); font-size: 16px; line-height: 24px; }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .chip { display: inline-flex; align-items: center; min-height: var(--tap); padding: 0 14px; border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--surface); font-size: 14px; color: var(--link); text-decoration: none; }
    .chips .muted { font-weight: 700; }
  `,
  template: `<article>
    @for (s of segments(); track $index) {
      @if (s.kind === 'code') {
        <va-code-block [code]="s.code" [language]="s.language" />
      } @else {
        <p>{{ s.text }}</p>
      }
    }
    @if (sources().length) {
      <div class="chips">
        <span class="muted">Sources</span>
        @for (src of sources(); track src.id) {
          @if (src.url) {
            <a class="chip" [href]="src.url" target="_blank" rel="noopener noreferrer">{{ src.title }}</a>
          } @else {
            <span class="chip">{{ src.title }}</span>
          }
        }
      </div>
    }
  </article>`,
})
export class AnswerCardComponent {
  readonly text = input.required<string>();
  readonly sources = input<readonly Source[]>([]);
  protected readonly segments = computed(() => parseAnswer(this.text()));
}
