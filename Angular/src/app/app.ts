import { ChangeDetectionStrategy, Component } from '@angular/core';
import { ShellComponent } from './core/shell/shell.component';

@Component({
  selector: 'va-root',
  imports: [ShellComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<va-shell />',
})
export class App {}
