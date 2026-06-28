import { useEffect, useRef } from "react";
import { useStore } from "../store";
import type { WaterfallMessage } from "../types/ws";
import { NYQUIST_HZ } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption } from "./chartAxis";
import { useCanvasSize, prepareContext } from "./canvas";

const HEIGHT = 300;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const TICK_HZ = 1000;
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

const FREQUENCY_AXIS = new FrequencyAxis(NYQUIST_HZ, TICK_HZ);

function drawAxis(ctx: CanvasRenderingContext2D, width: number): void {
  FREQUENCY_AXIS.draw(ctx, {
    width,
    tickTop: PLOT_HEIGHT,
    tickBottom: PLOT_HEIGHT + 4,
    labelY: HEIGHT - 6,
    labelInset: 12,
  });
  axisCaption(ctx, "Time (newer ↓)");
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

function buildSpectrogram(frames: WaterfallMessage[]): ImageData | null {
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

function drawHint(ctx: CanvasRenderingContext2D, width: number): void {
  ctx.fillStyle = HINT_COLOR;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

export function Waterfall() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const bufferRef = useRef<HTMLCanvasElement | null>(null);
  const frames = useStore((s) => s.waterfallFrames);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const ctx = prepareContext(canvas, size);
    if (!ctx) return;
    const image = buildSpectrogram(frames);
    if (image) {
      if (!bufferRef.current) bufferRef.current = document.createElement("canvas");
      scaleOnto(ctx, image, bufferRef.current, size.width);
    } else {
      drawHint(ctx, size.width);
    }
    drawAxis(ctx, size.width);
  }, [ref, frames, size.width, size.height]);

  return <canvas ref={ref} style={{ width: "100%", height: HEIGHT, display: "block" }} />;
}
