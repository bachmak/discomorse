import type { ResolvedTheme } from "../theme/themeChoice";
import { useResolvedTheme } from "../theme/themeStore";

export interface ChartPalette {
  trace: string;
  fill: string;
  guide: string;
  hint: string;
  label: string;
  tick: string;
  captionBackground: string;
}

const PALETTES: Record<ResolvedTheme, ChartPalette> = {
  dark: {
    trace: "#22d3ee",
    fill: "rgba(34, 211, 238, 0.22)",
    guide: "rgba(34, 211, 238, 0.16)",
    hint: "rgba(148, 163, 184, 0.75)",
    label: "rgba(148, 163, 184, 0.9)",
    tick: "rgba(34, 211, 238, 0.16)",
    captionBackground: "rgba(8, 11, 17, 0.7)",
  },
  light: {
    trace: "#0e7490",
    fill: "rgba(14, 116, 144, 0.18)",
    guide: "rgba(14, 116, 144, 0.25)",
    hint: "rgba(71, 85, 105, 0.8)",
    label: "rgba(51, 65, 85, 0.9)",
    tick: "rgba(14, 116, 144, 0.22)",
    captionBackground: "rgba(255, 255, 255, 0.75)",
  },
};

export function useChartPalette(): ChartPalette {
  return PALETTES[useResolvedTheme()];
}
