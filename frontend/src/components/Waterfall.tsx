import { useEffect, useRef } from "react";
import { useStore } from "../store";
import type { ToneSpectrumMessage } from "../types/ws";
import { NYQUIST_HZ } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import { Range } from "../charts/ticks";
import { VerticalScroll } from "../charts/gestures";
import { useChartPalette } from "../charts/palette";
import type { ChartSurface } from "../charts/surface";
import type { ItemWindow } from "../charts/viewport";
import { useViewport, type ViewportSetup } from "../hooks/useViewport";
import { useCanvasSize, prepareSurface } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";

const HEIGHT = 300;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const VISIBLE_FRAMES = 200;

const FREQUENCY_AXIS = new FrequencyAxis();
const FREQUENCY_RANGE = new Range(0, NYQUIST_HZ);

const WATERFALL_VIEW: ViewportSetup = {
  gesture: new VerticalScroll(),
  span: VISIBLE_FRAMES,
  limits: { min: VISIBLE_FRAMES, max: VISIBLE_FRAMES },
};

function geometry(width: number): AxisGeometry {
  return {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: HEIGHT - 6,
    labelInset: 14,
  };
}

function drawAxis(surface: ChartSurface, width: number): void {
  FREQUENCY_AXIS.draw(surface, FREQUENCY_RANGE, geometry(width));
  axisCaption(surface, "Time (newer ↓)");
}

type Rgb = readonly [number, number, number];

const PALETTE: readonly Rgb[] = [
  [9, 6, 50],
  [26, 14, 110],
  [64, 18, 150],
  [120, 28, 170],
  [186, 50, 150],
  [230, 90, 110],
  [250, 200, 90],
  [255, 255, 238],
];

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function mix(low: Rgb, high: Rgb, t: number): Rgb {
  return [
    low[0] + (high[0] - low[0]) * t,
    low[1] + (high[1] - low[1]) * t,
    low[2] + (high[2] - low[2]) * t,
  ];
}

function magnitudeColor(magnitude: number): Rgb {
  const scaled = clamp01(magnitude) * (PALETTE.length - 1);
  const low = Math.min(PALETTE.length - 2, Math.floor(scaled));
  return mix(PALETTE[low], PALETTE[low + 1], scaled - low);
}

function paintRow(image: ImageData, row: number, magnitudes: number[]): void {
  for (let x = 0; x < image.width; x++) {
    const [r, g, b] = magnitudeColor(magnitudes[x] ?? 0);
    const offset = (row * image.width + x) * 4;
    image.data.set([r, g, b, 255], offset);
  }
}

function visibleFrames(frames: ToneSpectrumMessage[], window: ItemWindow): ToneSpectrumMessage[] {
  return frames.slice(Math.max(0, Math.round(window.from)), Math.max(0, Math.round(window.to)));
}

function buildSpectrogram(frames: ToneSpectrumMessage[]): ImageData | null {
  const width = frames.length > 0 ? frames[frames.length - 1].data.length : 0;
  if (width === 0) return null;
  const image = new ImageData(width, frames.length);
  frames.forEach((frame, row) => paintRow(image, row, frame.data));
  return image;
}

function scaleOnto(
  ctx: CanvasRenderingContext2D,
  image: ImageData,
  buffer: HTMLCanvasElement,
  width: number,
): void {
  buffer.width = image.width;
  buffer.height = image.height;
  const bufferCtx = buffer.getContext("2d");
  if (!bufferCtx) return;
  bufferCtx.putImageData(image, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(buffer, 0, 0, width, PLOT_HEIGHT);
}

function drawHint({ ctx, palette }: ChartSurface, width: number): void {
  ctx.fillStyle = palette.hint;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

function drawWaterfall(
  surface: ChartSurface,
  frames: ToneSpectrumMessage[],
  buffer: HTMLCanvasElement,
  width: number,
): void {
  const image = buildSpectrogram(frames);
  if (image) scaleOnto(surface.ctx, image, buffer, width);
  else drawHint(surface, width);
  drawAxis(surface, width);
}

export function Waterfall() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const palette = useChartPalette();
  const bufferRef = useRef<HTMLCanvasElement | null>(null);
  const frames = useStore((s) => s.spectrumFrames);
  const { view, goLive } = useViewport(ref, frames.length, WATERFALL_VIEW);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    bufferRef.current ??= document.createElement("canvas");
    const visible = visibleFrames(frames, view.window(frames.length));
    if (surface) drawWaterfall(surface, visible, bufferRef.current, size.width);
  }, [ref, frames, view, size.width, size.height, palette]);

  return <ChartCanvas canvasRef={ref} height={HEIGHT} goLive={goLive} />;
}
