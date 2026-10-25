import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Source, SourceKind } from '../core/api/api.models';

const KIND_LABEL: Record<SourceKind, string> = {
  documentation: 'Documentation',
  article: 'Article',
  repository: 'Repository',
};

/** "Documentation · spring.io": the kind plus the origin host when the url is valid. */
export function describeSource(source: Source): string {
  const label = KIND_LABEL[source.kind];
  if (!source.url) return label;
  try {
    return `${label} · ${new URL(source.url).hostname.replace(/^www\./, '')}`;
  } catch {
    return label;
  }
}

@Component({
  selector: 'va-sources-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: `
    aside { display: flex; flex-direction: column; gap: 12px; padding: 20px 16px; background: var(--surface); border-left: 1px solid var(--line); }
    h2 { margin: 0 4px; font-size: 20px; font-weight: 800; }
    .card { display: flex; flex-direction: column; gap: 4px; padding: 14px; min-height: var(--tap); border: 1px solid var(--line); border-radius: var(--radius-card); text-decoration: none; color: inherit; }
    a.card:hover { border-color: var(--primary); }
    b { color: var(--link); font-size: 15px; }
    span { color: var(--muted); font-size: 13px; }
  `,
  template: `
    @if (sources().length) {
      <aside aria-label="Sources">
        <h2>Sources</h2>
        @for (s of sources(); track s.id) {
          @if (s.url) {
            <a class="card" [href]="s.url" target="_blank" rel="noopener noreferrer">
              <b>{{ s.title }}</b><span>{{ describe(s) }}</span>
            </a>
          } @else {
            <div class="card"><b>{{ s.title }}</b><span>{{ describe(s) }}</span></div>
          }
        }
      </aside>
    }
  `,
})
export class SourcesPanelComponent {
  readonly sources = input<readonly Source[]>([]);
  protected readonly describe = describeSource;
}
