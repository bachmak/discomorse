import type { ChartPalette } from "./palette";

export interface ChartSurface {
  ctx: CanvasRenderingContext2D;
  palette: ChartPalette;
}
