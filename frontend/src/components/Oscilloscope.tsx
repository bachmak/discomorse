import { useEffect } from "react";
import { useStore } from "../store";
import { HOP_RATE_HZ } from "../audioFormat";
import { MAX_KEYING_SAMPLES } from "../signals/history";
import { AXIS_HEIGHT, TimeAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import { Range } from "../charts/ticks";
import type { ChartViewSetup } from "../charts/chartView";
import { ZoomAndPan } from "../charts/gestures";
import { useChartPalette } from "../charts/palette";
import type { ChartSurface } from "../charts/surface";
import { Viewport } from "../charts/viewport";
import type { Bounds, ItemWindow } from "../charts/window";
import { useChartView } from "../hooks/useChartView";
import { useCanvasSize, prepareSurface } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const MID = PLOT_HEIGHT / 2;
const AMPLITUDE = MID * 0.9;

const TIME_AXIS = new TimeAxis();

const SCOPE_VIEW: ChartViewSetup<Viewport> = {
  gesture: new ZoomAndPan<Viewport>(),
  initial: new Viewport(4 * HOP_RATE_HZ),
  home: (view) => view.atLive(),
};

function scopeBounds(samples: number): Bounds {
  return { total: samples, limits: { min: 0.1 * HOP_RATE_HZ, max: MAX_KEYING_SAMPLES } };
}

function geometry(width: number): AxisGeometry {
  return {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: HEIGHT - 6,
    labelInset: 16,
  };
}

function secondsAgo(window: ItemWindow, total: number): Range {
  return new Range((window.from - total) / HOP_RATE_HZ, (window.to - total) / HOP_RATE_HZ);
}

function drawBaseline({ ctx, palette }: ChartSurface, width: number): void {
  ctx.strokeStyle = palette.guide;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, MID);
  ctx.lineTo(width, MID);
  ctx.stroke();
}

function columnPeak(levels: number[], from: number, to: number): number {
  const start = Math.max(0, Math.floor(from));
  const end = Math.min(levels.length, Math.max(start + 1, Math.floor(to)));
  let peak = 0;
  for (let i = start; i < end; i++) {
    const magnitude = Math.abs(levels[i]);
    if (magnitude > peak) peak = magnitude;
  }
  return peak;
}

function columnPeaks(levels: number[], window: ItemWindow, columns: number): number[] {
  const perColumn = (window.to - window.from) / columns;
  return Array.from({ length: columns }, (_unused, x) =>
    columnPeak(levels, window.from + x * perColumn, window.from + (x + 1) * perColumn),
  );
}

function drawWaveform(
  { ctx, palette }: ChartSurface,
  levels: number[],
  window: ItemWindow,
  width: number,
): void {
  const peaks = columnPeaks(levels, window, Math.round(width));
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

function drawScope(
  surface: ChartSurface,
  levels: number[],
  window: ItemWindow,
  width: number,
): void {
  drawBaseline(surface, width);
  TIME_AXIS.draw(surface, secondsAgo(window, levels.length), geometry(width));
  if (levels.length > 0) drawWaveform(surface, levels, window, width);
  else drawHint(surface, width);
  axisCaption(surface, "Key");
}

export function Oscilloscope() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const palette = useChartPalette();
  const levels = useStore((s) => s.keyingLevels);
  const { view, goHome } = useChartView(ref, scopeBounds(levels.length), SCOPE_VIEW);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    if (surface) drawScope(surface, levels, view.window(levels.length), size.width);
  }, [ref, levels, view, size.width, size.height, palette]);

  return <ChartCanvas canvasRef={ref} height={HEIGHT} onReset={goHome} />;
}
