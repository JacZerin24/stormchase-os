import { describe, expect, it } from 'vitest';
import { basemapStyle, resolveTheme } from './theme';

describe('display theme', () => {
  it('respects a saved explicit user choice over the OS preference', () => {
    expect(resolveTheme('light',true)).toBe('light');
    expect(resolveTheme('dark',false)).toBe('dark');
  });
  it('defaults to operating system appearance without a valid saved choice', () => {
    expect(resolveTheme(null,true)).toBe('dark');
    expect(resolveTheme('invalid',false)).toBe('light');
  });
  it('uses distinct CARTO light and dark styles', () => {
    expect(basemapStyle('light')).toContain('positron-gl-style');
    expect(basemapStyle('dark')).toContain('dark-matter-gl-style');
    expect(basemapStyle('light')).not.toBe(basemapStyle('dark'));
  });
});
