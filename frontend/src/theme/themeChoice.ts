export type ThemeChoice = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

const CYCLE: readonly ThemeChoice[] = ["system", "light", "dark"];

export const DEFAULT_CHOICE: ThemeChoice = "system";

export function nextChoice(current: ThemeChoice): ThemeChoice {
  return CYCLE[(CYCLE.indexOf(current) + 1) % CYCLE.length];
}

export function isThemeChoice(value: string | null): value is ThemeChoice {
  return CYCLE.includes(value as ThemeChoice);
}
