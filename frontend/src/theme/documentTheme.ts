import type { ThemeChoice } from "./themeChoice";

/** The stylesheet follows the system unless the root element pins a scheme. */
export function applyThemeChoice(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") delete root.dataset.theme;
  else root.dataset.theme = choice;
}
