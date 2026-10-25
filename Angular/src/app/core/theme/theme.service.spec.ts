import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeService } from './theme.service';

function stubSystemScheme(dark: boolean): void {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: dark && query.includes('dark'),
    media: query,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
}

describe('ThemeService', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });
  afterEach(() => vi.unstubAllGlobals());

  it('defaults to light when the system prefers light', () => {
    stubSystemScheme(false);
    const svc = TestBed.inject(ThemeService);
    expect(svc.theme()).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('defaults to dark when the system prefers dark', () => {
    stubSystemScheme(true);
    expect(TestBed.inject(ThemeService).theme()).toBe('dark');
  });

  it('prefers the persisted choice over the system scheme', () => {
    stubSystemScheme(true);
    localStorage.setItem('va-theme', 'light');
    expect(TestBed.inject(ThemeService).theme()).toBe('light');
  });

  it('ignores invalid persisted values', () => {
    stubSystemScheme(false);
    localStorage.setItem('va-theme', 'purple');
    expect(TestBed.inject(ThemeService).theme()).toBe('light');
  });

  it('set() updates the signal, data-theme and storage', () => {
    stubSystemScheme(false);
    const svc = TestBed.inject(ThemeService);
    svc.set('dark');
    expect(svc.theme()).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorage.getItem('va-theme')).toBe('dark');
  });

  it('toggle() flips the theme', () => {
    stubSystemScheme(false);
    const svc = TestBed.inject(ThemeService);
    svc.toggle();
    expect(svc.theme()).toBe('dark');
    svc.toggle();
    expect(svc.theme()).toBe('light');
  });

  it('survives a throwing localStorage', () => {
    stubSystemScheme(true);
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('denied');
      },
      setItem: () => {
        throw new Error('denied');
      },
    });
    const svc = TestBed.inject(ThemeService);
    expect(svc.theme()).toBe('dark');
    expect(() => svc.set('light')).not.toThrow();
    expect(svc.theme()).toBe('light');
  });
});
