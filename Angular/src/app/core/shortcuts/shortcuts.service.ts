import { DOCUMENT } from '@angular/common';
import { DestroyRef, Injectable, inject } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ShortcutsService {
  private readonly doc = inject(DOCUMENT);
  private readonly start = new Subject<void>();
  private readonly cancel = new Subject<void>();

  /** Ctrl+Shift+M */
  readonly start$: Observable<void> = this.start.asObservable();
  /** Esc */
  readonly cancel$: Observable<void> = this.cancel.asObservable();

  constructor() {
    const handler = (e: Event): void => this.onKey(e as KeyboardEvent);
    this.doc.addEventListener('keydown', handler);
    inject(DestroyRef).onDestroy(() => {
      this.doc.removeEventListener('keydown', handler);
      this.start.complete();
      this.cancel.complete();
    });
  }

  private onKey(e: KeyboardEvent): void {
    if (e.ctrlKey && e.shiftKey && (e.code === 'KeyM' || e.key.toLowerCase() === 'm')) {
      e.preventDefault();
      this.start.next();
    } else if (e.key === 'Escape') {
      this.cancel.next();
    }
  }
}
