import { create } from "zustand";
import { applyThemeChoice } from "./documentTheme";
import { systemTheme } from "./systemTheme";
import { nextChoice, type ResolvedTheme, type ThemeChoice } from "./themeChoice";
import { loadThemeChoice, saveThemeChoice } from "./themeStorage";

interface ThemeState {
  choice: ThemeChoice;
  system: ResolvedTheme;
  cycleTheme: () => void;
  observeSystemTheme: () => void;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  choice: loadThemeChoice(),
  system: systemTheme(),

  cycleTheme: () => {
    const choice = nextChoice(get().choice);
    saveThemeChoice(choice);
    applyThemeChoice(choice);
    set({ choice });
  },

  observeSystemTheme: () => set({ system: systemTheme() }),
}));

export function useResolvedTheme(): ResolvedTheme {
  return useThemeStore((s) => (s.choice === "system" ? s.system : s.choice));
}

export function initTheme(): void {
  applyThemeChoice(useThemeStore.getState().choice);
}
