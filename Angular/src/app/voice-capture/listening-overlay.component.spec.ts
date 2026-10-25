import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ListeningOverlayComponent } from './listening-overlay.component';

function stubReducedMotion(reduce: boolean): void {
  vi.stubGlobal('matchMedia', (q: string) => ({ matches: reduce && q.includes('reduce'), media: q }));
}

describe('ListeningOverlayComponent', () => {
  let fixture: ComponentFixture<ListeningOverlayComponent>;
  const el = (): HTMLElement => fixture.nativeElement as HTMLElement;

  async function create(reduce = false): Promise<void> {
    stubReducedMotion(reduce);
    fixture = TestBed.createComponent(ListeningOverlayComponent);
    fixture.componentRef.setInput('levels', [0.1, 0.5, 1]);
    fixture.componentRef.setInput('secondsLeft', 12);
    fixture.componentRef.setInput('totalSeconds', 30);
    await fixture.whenStable();
  }
  afterEach(() => vi.unstubAllGlobals());

  it('announces "Listening…" with role=status', async () => {
    await create();
    const status = el().querySelector('[role="status"]');
    expect(status?.textContent).toContain('Listening…');
  });

  it('shows the auto-stop countdown', async () => {
    await create();
    expect(el().textContent).toContain('Auto-stop in 12 s');
  });

  it('renders one bar per level and hides them from assistive tech', async () => {
    await create();
    expect(el().querySelectorAll('.wave b').length).toBe(3);
    expect(el().querySelector('.wave')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('flags reduced motion so animation is disabled', async () => {
    await create(true);
    expect(el().querySelector('.wave')?.classList.contains('reduced')).toBe(true);
  });

  it('does not flag reduced motion by default', async () => {
    await create(false);
    expect(el().querySelector('.wave')?.classList.contains('reduced')).toBe(false);
  });

  it('Cancel emits cancelled and Done emits done', async () => {
    await create();
    const cancelled = vi.fn();
    const done = vi.fn();
    fixture.componentInstance.cancelled.subscribe(cancelled);
    fixture.componentInstance.done.subscribe(done);
    (el().querySelector('button.btn') as HTMLButtonElement).click();
    (el().querySelector('button[aria-label="Done, stop listening"]') as HTMLButtonElement).click();
    expect(cancelled).toHaveBeenCalledTimes(1);
    expect(done).toHaveBeenCalledTimes(1);
  });
});
