import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

type Palette = Record<string, string>;

function parseBlock(css: string, selector: RegExp): Palette {
  const block = selector.exec(css)?.[1] ?? '';
  const out: Palette = {};
  for (const m of block.matchAll(/--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\s*;/g)) {
    out[m[1] as string] = m[2] as string;
  }
  return out;
}

function luminance(hex: string): number {
  const h = hex.length === 4 ? '#' + [...hex.slice(1)].map((c) => c + c).join('') : hex;
  const [r, g, b] = [1, 3, 5].map((i) => {
    const v = parseInt(h.slice(i, i + 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

const css = readFileSync(resolve(process.cwd(), 'src/styles/tokens.scss'), 'utf8');
const light = parseBlock(css, /:root\s*\{([^}]*)\}/);
const dark = { ...light, ...parseBlock(css, /\[data-theme=['"]?dark['"]?\]\s*\{([^}]*)\}/) };

/** [foreground token, background token, minimum ratio] -- 4.5 text, 3 non-text/large (WCAG 2.2 AA). */
const PAIRS: ReadonlyArray<readonly [string, string, number]> = [
  ['ink', 'bg', 4.5],
  ['ink', 'surface', 4.5],
  ['ink2', 'surface', 4.5],
  ['muted', 'surface', 4.5],
  ['muted', 'bg', 4.5],
  ['link', 'surface', 4.5],
  ['link', 'bg', 4.5],
  ['on-primary', 'primary', 4.5],
  ['ink', 'field', 4.5],
  ['ac', 'bg', 3],
  ['ac', 'surface', 3],
  ['primary', 'bg', 3],
];

describe.each([
  ['light', light],
  ['dark', dark],
])('WCAG 2.2 AA contrast (%s)', (_name, palette) => {
  it.each(PAIRS)('%s on %s >= %f:1', (fg, bg, min) => {
    expect(palette[fg], `token --${fg}`).toBeDefined();
    expect(palette[bg], `token --${bg}`).toBeDefined();
    expect(contrast(palette[fg] as string, palette[bg] as string)).toBeGreaterThanOrEqual(min);
  });
});
