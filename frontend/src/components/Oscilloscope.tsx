import { useEffect } from "react";
import { useStore, MAX_SCOPE_SAMPLES } from "../store";
import { SCOPE_RATE_HZ } from "../audioFormat";
import { AXIS_HEIGHT, TimeAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import { Range } from "../charts/ticks";
import { ZoomAndPan } from "../charts/gestures";
import type { ItemWindow } from "../charts/viewport";
import { useViewport, type ViewportSetup } from "../hooks/useViewport";
import { useCanvasSize, prepareContext } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const MID = PLOT_HEIGHT / 2;
const AMPLITUDE = MID * 0.9;
const TRACE_COLOR = "#22d3ee";
const FILL_COLOR = "rgba(34, 211, 238, 0.22)";
const GUIDE_COLOR = "rgba(34, 211, 238, 0.16)";
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

const TIME_AXIS = new TimeAxis();

const SCOPE_VIEW: ViewportSetup = {
  gesture: new ZoomAndPan(),
  span: 4 * SCOPE_RATE_HZ,
  limits: { min: 0.1 * SCOPE_RATE_HZ, max: MAX_SCOPE_SAMPLES },
};

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
  return new Range((window.from - total) / SCOPE_RATE_HZ, (window.to - total) / SCOPE_RATE_HZ);
}

function drawBaseline(ctx: CanvasRenderingContext2D, width: number): void {
  ctx.strokeStyle = GUIDE_COLOR;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, MID);
  ctx.lineTo(width, MID);
  ctx.stroke();
}

function columnPeak(samples: number[], from: number, to: number): number {
  const start = Math.max(0, Math.floor(from));
  const end = Math.min(samples.length, Math.max(start + 1, Math.floor(to)));
  let peak = 0;
  for (let i = start; i < end; i++) {
    const magnitude = Math.abs(samples[i]);
    if (magnitude > peak) peak = magnitude;
  }
  return peak;
}

function columnPeaks(samples: number[], window: ItemWindow, columns: number): number[] {
  const perColumn = (window.to - window.from) / columns;
  return Array.from({ length: columns }, (_unused, x) =>
    columnPeak(samples, window.from + x * perColumn, window.from + (x + 1) * perColumn),
  );
}

function drawWaveform(
  ctx: CanvasRenderingContext2D,
  samples: number[],
  window: ItemWindow,
  width: number,
): void {
  const peaks = columnPeaks(samples, window, Math.round(width));
  ctx.beginPath();
  peaks.forEach((peak, x) => ctx.lineTo(x, MID - peak * AMPLITUDE));
  for (let x = peaks.length - 1; x >= 0; x--) ctx.lineTo(x, MID + peaks[x] * AMPLITUDE);
  ctx.closePath();
  ctx.fillStyle = FILL_COLOR;
  ctx.fill();
  ctx.strokeStyle = TRACE_COLOR;
  ctx.lineWidth = 1;
  ctx.stroke();
}

function drawHint(ctx: CanvasRenderingContext2D, width: number): void {
  ctx.fillStyle = HINT_COLOR;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, MID - 8);
}

function drawScope(
  ctx: CanvasRenderingContext2D,
  samples: number[],
  window: ItemWindow,
  width: number,
): void {
  drawBaseline(ctx, width);
  TIME_AXIS.draw(ctx, secondsAgo(window, samples.length), geometry(width));
  if (samples.length > 0) drawWaveform(ctx, samples, window, width);
  else drawHint(ctx, width);
  axisCaption(ctx, "Amplitude");
}

export function Oscilloscope() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const samples = useStore((s) => s.scopeSamples);
  const { view, goLive } = useViewport(ref, samples.length, SCOPE_VIEW);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const ctx = prepareContext(canvas, size);
    if (ctx) drawScope(ctx, samples, view.window(samples.length), size.width);
  }, [ref, samples, view, size.width, size.height]);

  return <ChartCanvas canvasRef={ref} height={HEIGHT} goLive={goLive} />;
}
