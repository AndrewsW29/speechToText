import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import { IconComponent } from './icon.component';

export interface Token {
  readonly text: string;
  readonly cls: '' | 'k' | 'a' | 't' | 's';
}

const KEYWORDS = new Set(
  ('public private protected class interface enum extends implements return new static final void import package ' +
    'if else for while try catch throw throws const let var function def async await from export default int boolean ' +
    'string this super null true false record').split(' '),
);

export function tokenize(code: string): Token[] {
  const re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(@\w+)|(\b[A-Z]\w*\b)|(\b[a-z_]\w*\b)|([\s\S])/g;
  const out: { text: string; cls: Token['cls'] }[] = [];
  for (const m of code.matchAll(re)) {
    const cls: Token['cls'] = m[1] ? 's' : m[2] ? 'a' : m[3] ? 't' : m[4] && KEYWORDS.has(m[4]) ? 'k' : '';
    const last = out[out.length - 1];
    if (last && last.cls === cls) last.text += m[0];
    else out.push({ text: m[0], cls });
  }
  return out;
}

@Component({
  selector: 'va-code-block',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    :host { display: block; }
    .cb { border-radius: var(--radius-card); overflow: hidden; border: 1px solid var(--line); }
    .ch { display: flex; align-items: center; justify-content: space-between; padding: 2px 4px 2px 14px; background: var(--code-head); color: var(--code-muted); font-size: 12px; }
    button { display: inline-flex; align-items: center; gap: 6px; min-height: var(--tap); padding: 0 10px; border: 0; background: none; color: var(--code-ink); font-size: 13px; }
    pre { margin: 0; padding: 12px 14px; background: var(--code-bg); color: var(--code-ink); font: 13px/20px var(--font-mono); overflow-x: auto; }
    .k { color: var(--tok-k); } .a { color: var(--tok-a); } .t { color: var(--tok-t); } .s { color: var(--tok-s); }
  `,
  template: `<div class="cb">
    <div class="ch">
      <span>{{ language() }}</span>
      <button type="button" aria-label="Copy code" (click)="copy()">
        <va-icon [name]="copied() ? 'check' : 'copy'" [size]="16" />{{ copied() ? 'Copied' : 'Copy' }}
      </button>
    </div>
    <pre><code>@for (t of tokens(); track $index) {<span [class]="t.cls">{{ t.text }}</span>}</code></pre>
  </div>`,
})
export class CodeBlockComponent {
  readonly code = input.required<string>();
  readonly language = input('');
  protected readonly copied = signal(false);
  protected readonly tokens = computed(() => tokenize(this.code()));

  protected async copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.code());
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    } catch {
      this.copied.set(false);
    }
  }
}
