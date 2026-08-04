import type { ResolvedTheme } from "./themeChoice";

const DARK_QUERY = "(prefers-color-scheme: dark)";

export function systemTheme(): ResolvedTheme {
  return window.matchMedia(DARK_QUERY).matches ? "dark" : "light";
}

export function onSystemThemeChange(notify: () => void): () => void {
  const query = window.matchMedia(DARK_QUERY);
  query.addEventListener("change", notify);
  return () => query.removeEventListener("change", notify);
}
