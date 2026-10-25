import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { Source } from '../core/api/api.models';
import { AnswerCardComponent } from './answer-card.component';
import { SourcesPanelComponent, describeSource } from './sources-panel.component';

const SOURCES: Source[] = [
  { id: 'a', title: 'Spring Docs: Building a REST service', url: 'https://spring.io/guides/rest', kind: 'documentation' },
  { id: 'b', title: 'users-service / UserController', url: 'https://github.com/acme/users', kind: 'repository' },
  { id: 'c', title: 'Offline note', url: null, kind: 'article' },
];

describe('describeSource', () => {
  it('labels the kind and the origin host', () => {
    expect(describeSource(SOURCES[0]!)).toBe('Documentation · spring.io');
    expect(describeSource(SOURCES[1]!)).toBe('Repository · github.com');
  });

  it('falls back to the kind when there is no url or the url is invalid', () => {
    expect(describeSource(SOURCES[2]!)).toBe('Article');
    expect(describeSource({ ...SOURCES[2]!, url: 'not a url' })).toBe('Article');
  });
});

describe('SourcesPanelComponent', () => {
  let fixture: ComponentFixture<SourcesPanelComponent>;
  const el = (): HTMLElement => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    fixture = TestBed.createComponent(SourcesPanelComponent);
    fixture.componentRef.setInput('sources', SOURCES);
    fixture.detectChanges();
  });

  it('renders a landmark with a card per source', () => {
    expect(el().querySelector('aside[aria-label="Sources"]')).toBeTruthy();
    expect(el().querySelectorAll('.card')).toHaveLength(3);
  });

  it('opens linked sources in a new tab without leaking the opener', () => {
    const link = el().querySelector<HTMLAnchorElement>('a.card')!;
    expect(link.getAttribute('href')).toBe('https://spring.io/guides/rest');
    expect(link.target).toBe('_blank');
    expect(link.rel).toContain('noopener');
    expect(link.textContent).toContain('Documentation · spring.io');
  });

  it('shows sources without a url as plain cards', () => {
    expect(el().querySelectorAll('a.card')).toHaveLength(2);
    expect(el().querySelectorAll('div.card')).toHaveLength(1);
  });

  it('renders nothing when there are no sources', () => {
    fixture.componentRef.setInput('sources', []);
    fixture.detectChanges();
    expect(el().querySelector('aside')).toBeNull();
  });
});

describe('AnswerCardComponent source chips', () => {
  it('lists source chips inside the answer card', () => {
    const fixture = TestBed.createComponent(AnswerCardComponent);
    fixture.componentRef.setInput('text', 'Use a service.');
    fixture.componentRef.setInput('sources', SOURCES);
    fixture.detectChanges();
    const chips = (fixture.nativeElement as HTMLElement).querySelectorAll('.chips .chip');
    expect(chips).toHaveLength(3);
    expect(chips[0]!.getAttribute('href')).toBe('https://spring.io/guides/rest');
  });
});
