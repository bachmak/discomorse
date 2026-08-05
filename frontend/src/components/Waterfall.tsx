import { useEffect, useRef } from "react";
import { useStore } from "../store";
import type { ToneSpectrumMessage } from "../types/ws";
import { NYQUIST_HZ } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import type { ChartViewSetup } from "../charts/chartView";
import { VerticalPan } from "../charts/gestures";
import { useChartPalette } from "../charts/palette";
import { Spectrogram } from "../charts/spectrogram";
import type { ChartSurface } from "../charts/surface";
import { Range } from "../charts/ticks";
import { Viewport } from "../charts/viewport";
import type { Bounds, ItemWindow } from "../charts/window";
import { useChartView } from "../hooks/useChartView";
import { useCanvasSize, prepareSurface } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";
import { BAND_BOUNDS, BAND_VIEW } from "./frequencyBand";

const HEIGHT = 300;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const VISIBLE_FRAMES = 200;

const FREQUENCY_AXIS = new FrequencyAxis();
const FULL_BAND = new Range(0, NYQUIST_HZ);

const TIME_VIEW: ChartViewSetup<Viewport> = {
  gesture: new VerticalPan<Viewport>(),
  initial: new Viewport(VISIBLE_FRAMES),
  home: (view) => view.atLive(),
};

function timeBounds(frames: number): Bounds {
  return { total: frames, limits: { min: VISIBLE_FRAMES, max: VISIBLE_FRAMES } };
}

function geometry(width: number): AxisGeometry {
  return {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: HEIGHT - 6,
    labelInset: 14,
  };
}

function drawAxis(surface: ChartSurface, band: Range, width: number): void {
  FREQUENCY_AXIS.draw(surface, band, geometry(width));
  axisCaption(surface, "Time (newer ↓)");
}

function visibleRows(frames: ToneSpectrumMessage[], window: ItemWindow): number[][] {
  const from = Math.max(0, Math.round(window.from));
  return frames.slice(from, Math.max(0, Math.round(window.to))).map((frame) => frame.data);
}

function visibleBins(band: Range): ItemWindow {
  return { from: FULL_BAND.fractionOf(band.min), to: FULL_BAND.fractionOf(band.max) };
}

function drawHint({ ctx, palette }: ChartSurface, width: number): void {
  ctx.fillStyle = palette.hint;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

function drawWaterfall(
  surface: ChartSurface,
  rows: number[][],
  spectrogram: Spectrogram,
  band: Range,
  width: number,
): void {
  const plot = { width, height: PLOT_HEIGHT };
  if (rows.length > 0) spectrogram.draw(surface.ctx, rows, visibleBins(band), plot);
  else drawHint(surface, width);
  drawAxis(surface, band, width);
}

export function Waterfall() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const palette = useChartPalette();
  const spectrogram = useRef<Spectrogram | null>(null);
  const frames = useStore((s) => s.spectrumFrames);
  const { view: time, goHome: goLive } = useChartView(ref, timeBounds(frames.length), TIME_VIEW);
  const { view: band, goHome: resetBand } = useChartView(ref, BAND_BOUNDS, BAND_VIEW);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    spectrogram.current ??= new Spectrogram();
    const rows = visibleRows(frames, time.window(frames.length));
    if (surface) drawWaterfall(surface, rows, spectrogram.current, band.range, size.width);
  }, [ref, frames, time, band, size.width, size.height, palette]);

  const reset = () => {
    goLive();
    resetBand();
  };

  return <ChartCanvas canvasRef={ref} height={HEIGHT} onReset={reset} />;
}
