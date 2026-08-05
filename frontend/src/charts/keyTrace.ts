import { AXIS_HEIGHT, TimeAxis, axisCaption, type AxisGeometry } from "./axis";
import { columnMeans } from "./columns";
import type { ChartSurface } from "./surface";
import type { Range } from "./ticks";
import type { ItemWindow } from "./window";

export const SCOPE_HEIGHT = 150;

const PLOT_HEIGHT = SCOPE_HEIGHT - AXIS_HEIGHT;
const MID = PLOT_HEIGHT / 2;
const AMPLITUDE = MID * 0.9;

const TIME_AXIS = new TimeAxis();

/** The stretch of key trace one frame shows: which samples, and where they sit in time. */
export interface ScopePlot {
  levels: readonly number[];
  window: ItemWindow;
  elapsed: Range;
  width: number;
}

function geometry(width: number): AxisGeometry {
  return {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: SCOPE_HEIGHT - 6,
    labelInset: 16,
  };
}

function drawBaseline({ ctx, palette }: ChartSurface, width: number): void {
  ctx.strokeStyle = palette.guide;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, MID);
  ctx.lineTo(width, MID);
  ctx.stroke();
}

function drawWaveform({ ctx, palette }: ChartSurface, plot: ScopePlot): void {
  const peaks = columnMeans(plot.levels, plot.window, Math.round(plot.width));
  ctx.beginPath();
  peaks.forEach((peak, x) => ctx.lineTo(x, MID - peak * AMPLITUDE));
  for (let x = peaks.length - 1; x >= 0; x--) ctx.lineTo(x, MID + peaks[x] * AMPLITUDE);
  ctx.closePath();
  ctx.fillStyle = palette.fill;
  ctx.fill();
  ctx.strokeStyle = palette.trace;
  ctx.lineWidth = 1;
  ctx.stroke();
}

function drawHint({ ctx, palette }: ChartSurface, width: number): void {
  ctx.fillStyle = palette.hint;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, MID - 8);
}

export function drawScope(surface: ChartSurface, plot: ScopePlot): void {
  drawBaseline(surface, plot.width);
  TIME_AXIS.draw(surface, plot.elapsed, geometry(plot.width));
  if (plot.levels.length > 0) drawWaveform(surface, plot);
  else drawHint(surface, plot.width);
  axisCaption(surface, "Key");
}
