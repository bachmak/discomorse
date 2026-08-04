import { useEffect } from "react";
import { useStore } from "../store";
import { NYQUIST_HZ } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import { Range } from "../charts/ticks";
import { useChartPalette } from "../charts/palette";
import type { ChartSurface } from "../charts/surface";
import { useCanvasSize, prepareSurface } from "./canvas";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;

const FREQUENCY_AXIS = new FrequencyAxis();
const FREQUENCY_RANGE = new Range(0, NYQUIST_HZ);

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function geometry(width: number): AxisGeometry {
  return { width, tickTop: 0, tickBottom: PLOT_HEIGHT, labelY: HEIGHT - 6, labelInset: 14 };
}

function drawSpectrum({ ctx, palette }: ChartSurface, data: number[], width: number): void {
  const denom = Math.max(1, data.length - 1);
  ctx.beginPath();
  ctx.moveTo(0, PLOT_HEIGHT);
  data.forEach((mag, i) => ctx.lineTo((i / denom) * width, PLOT_HEIGHT - clamp01(mag) * PLOT_HEIGHT));
  ctx.lineTo(width, PLOT_HEIGHT);
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
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

function drawFrame(surface: ChartSurface, data: number[], width: number): void {
  FREQUENCY_AXIS.draw(surface, FREQUENCY_RANGE, geometry(width));
  if (data.length > 0) drawSpectrum(surface, data, width);
  else drawHint(surface, width);
  axisCaption(surface, "Magnitude");
}

export function FFTSpectrum() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const palette = useChartPalette();
  const frame = useStore((s) => s.spectrumFrames[s.spectrumFrames.length - 1]);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    if (surface) drawFrame(surface, frame?.data ?? [], size.width);
  }, [ref, frame, size.width, size.height, palette]);

  return <canvas ref={ref} style={{ height: HEIGHT }} />;
}
