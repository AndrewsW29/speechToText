import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'va-section-placeholder',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p class="muted" style="padding: 32px">This section is coming soon.</p>`,
})
export class SectionPlaceholderComponent {}
