import { useEffect } from "react";
import { useStore, MAX_SCOPE_SAMPLES } from "../store";
import { WS_SAMPLE_RATE_HZ } from "../audioFormat";
import { AXIS_HEIGHT, TimeAxis, axisCaption } from "./chartAxis";
import { useCanvasSize, prepareContext } from "./canvas";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const MID = PLOT_HEIGHT / 2;
const AMPLITUDE = MID * 0.9;
const WINDOW_MS = (MAX_SCOPE_SAMPLES / WS_SAMPLE_RATE_HZ) * 1000;
const TICK_MS = WINDOW_MS / 4;
const TRACE_COLOR = "#22d3ee";
const FILL_COLOR = "rgba(34, 211, 238, 0.22)";
const GUIDE_COLOR = "rgba(34, 211, 238, 0.16)";
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

const TIME_AXIS = new TimeAxis(WINDOW_MS, TICK_MS);

function drawBaseline(ctx: CanvasRenderingContext2D, width: number): void {
  ctx.strokeStyle = GUIDE_COLOR;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, MID);
  ctx.lineTo(width, MID);
  ctx.stroke();
}

function drawAxis(ctx: CanvasRenderingContext2D, width: number): void {
  TIME_AXIS.draw(ctx, {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: HEIGHT - 6,
    labelInset: 14,
  });
}

function columnPeak(samples: number[], from: number, to: number): number {
  const start = Math.floor(from);
  const end = Math.min(samples.length, Math.max(start + 1, Math.floor(to)));
  let peak = 0;
  for (let i = start; i < end; i++) {
    const magnitude = Math.abs(samples[i]);
    if (magnitude > peak) peak = magnitude;
  }
  return peak;
}

function columnPeaks(samples: number[], columns: number): number[] {
  const perColumn = samples.length / columns;
  return Array.from({ length: columns }, (_unused, x) =>
    columnPeak(samples, x * perColumn, (x + 1) * perColumn),
  );
}

function drawWaveform(ctx: CanvasRenderingContext2D, samples: number[], width: number): void {
  const peaks = columnPeaks(samples, Math.round(width));
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

export function Oscilloscope() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const samples = useStore((s) => s.scopeSamples);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const ctx = prepareContext(canvas, size);
    if (!ctx) return;
    drawBaseline(ctx, size.width);
    drawAxis(ctx, size.width);
    if (samples.length > 0) drawWaveform(ctx, samples, size.width);
    else drawHint(ctx, size.width);
    axisCaption(ctx, "Amplitude");
  }, [ref, samples, size.width, size.height]);

  return <canvas ref={ref} style={{ width: "100%", height: HEIGHT, display: "block" }} />;
}
