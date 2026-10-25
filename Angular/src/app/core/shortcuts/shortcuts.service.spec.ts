import { TestBed } from '@angular/core/testing';
import { describe, expect, it, vi } from 'vitest';
import { ShortcutsService } from './shortcuts.service';

function press(init: KeyboardEventInit): KeyboardEvent {
  const event = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init });
  document.dispatchEvent(event);
  return event;
}

describe('ShortcutsService', () => {
  it('emits start$ on Ctrl+Shift+M and prevents default', () => {
    const svc = TestBed.inject(ShortcutsService);
    const spy = vi.fn();
    svc.start$.subscribe(spy);
    const event = press({ key: 'M', code: 'KeyM', ctrlKey: true, shiftKey: true });
    expect(spy).toHaveBeenCalledTimes(1);
    expect(event.defaultPrevented).toBe(true);
  });

  it('does not emit start$ for M without both modifiers', () => {
    const svc = TestBed.inject(ShortcutsService);
    const spy = vi.fn();
    svc.start$.subscribe(spy);
    press({ key: 'm', code: 'KeyM', ctrlKey: true });
    press({ key: 'M', code: 'KeyM', shiftKey: true });
    press({ key: 'm', code: 'KeyM' });
    expect(spy).not.toHaveBeenCalled();
  });

  it('emits cancel$ on Escape', () => {
    const svc = TestBed.inject(ShortcutsService);
    const spy = vi.fn();
    svc.cancel$.subscribe(spy);
    press({ key: 'Escape', code: 'Escape' });
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('stops listening after the injector is destroyed', () => {
    const svc = TestBed.inject(ShortcutsService);
    const spy = vi.fn();
    svc.cancel$.subscribe(spy);
    TestBed.resetTestingModule();
    press({ key: 'Escape', code: 'Escape' });
    expect(spy).not.toHaveBeenCalled();
  });
});
