import { useEffect } from "react";
import { onSystemThemeChange } from "./systemTheme";
import type { ThemeChoice } from "./themeChoice";
import { useThemeStore } from "./themeStore";

interface Theme {
  choice: ThemeChoice;
  cycle: () => void;
}

export function useTheme(): Theme {
  const choice = useThemeStore((s) => s.choice);
  const cycle = useThemeStore((s) => s.cycleTheme);
  const observeSystemTheme = useThemeStore((s) => s.observeSystemTheme);

  useEffect(() => onSystemThemeChange(observeSystemTheme), [observeSystemTheme]);

  return { choice, cycle };
}
