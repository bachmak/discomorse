import { DEFAULT_CHOICE, isThemeChoice, type ThemeChoice } from "./themeChoice";

const STORAGE_KEY = "discomorse:theme";

export function loadThemeChoice(): ThemeChoice {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isThemeChoice(stored) ? stored : DEFAULT_CHOICE;
}

export function saveThemeChoice(choice: ThemeChoice): void {
  window.localStorage.setItem(STORAGE_KEY, choice);
}
