import { useEffect } from "react";
import { useStore } from "../store";
import { NYQUIST_HZ } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption } from "./chartAxis";
import { useCanvasSize, prepareContext } from "./canvas";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const TICK_HZ = 1000;
const TRACE_COLOR = "#22d3ee";
const FILL_COLOR = "rgba(34, 211, 238, 0.22)";
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

const FREQUENCY_AXIS = new FrequencyAxis(NYQUIST_HZ, TICK_HZ);

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function drawAxis(ctx: CanvasRenderingContext2D, width: number): void {
  FREQUENCY_AXIS.draw(ctx, {
    width,
    tickTop: 0,
    tickBottom: PLOT_HEIGHT,
    labelY: HEIGHT - 6,
    labelInset: 12,
  });
}

function drawSpectrum(ctx: CanvasRenderingContext2D, data: number[], width: number): void {
  const denom = Math.max(1, data.length - 1);
  ctx.beginPath();
  ctx.moveTo(0, PLOT_HEIGHT);
  data.forEach((mag, i) => ctx.lineTo((i / denom) * width, PLOT_HEIGHT - clamp01(mag) * PLOT_HEIGHT));
  ctx.lineTo(width, PLOT_HEIGHT);
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
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

export function FFTSpectrum() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const frame = useStore((s) => s.fftFrame);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const ctx = prepareContext(canvas, size);
    if (!ctx) return;
    drawAxis(ctx, size.width);
    if (frame && frame.data.length > 0) drawSpectrum(ctx, frame.data, size.width);
    else drawHint(ctx, size.width);
    axisCaption(ctx, "Magnitude");
  }, [ref, frame, size.width, size.height]);

  return <canvas ref={ref} style={{ width: "100%", height: HEIGHT, display: "block" }} />;
}
