export type DisplayTheme = 'dark' | 'light';
export const THEME_STORAGE_KEY = 'stormchase-os-theme';

export const BASEMAP_STYLES: Record<DisplayTheme,string> = {
  dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
};

export function basemapStyle(theme: DisplayTheme): string {
  return BASEMAP_STYLES[theme];
}

export function resolveTheme(saved: string | null, prefersDark: boolean): DisplayTheme {
  if (saved === 'dark' || saved === 'light') return saved;
  return prefersDark ? 'dark' : 'light';
}

export function getInitialTheme(): DisplayTheme {
  if (typeof window === 'undefined') return 'dark';
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? true;
  try { return resolveTheme(window.localStorage.getItem(THEME_STORAGE_KEY),prefersDark); }
  catch { return resolveTheme(null,prefersDark); }
}
