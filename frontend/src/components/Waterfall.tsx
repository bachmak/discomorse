import { useEffect, useRef } from "react";
import { useStore } from "../store";
import type { WaterfallMessage } from "../types/ws";

const WIDTH = 800;
const HEIGHT = 300;
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

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

function scaleOnto(ctx: CanvasRenderingContext2D, image: ImageData, buffer: HTMLCanvasElement): void {
  buffer.width = image.width;
  buffer.height = image.height;
  const bufferCtx = buffer.getContext("2d");
  if (!bufferCtx) return;
  bufferCtx.putImageData(image, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(buffer, 0, 0, WIDTH, HEIGHT);
}

function drawHint(ctx: CanvasRenderingContext2D): void {
  ctx.fillStyle = HINT_COLOR;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", WIDTH / 2, HEIGHT / 2);
}

export function Waterfall() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bufferRef = useRef<HTMLCanvasElement | null>(null);
  const frames = useStore((s) => s.waterfallFrames);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    const image = buildSpectrogram(frames);
    if (!image) {
      drawHint(ctx);
      return;
    }
    if (!bufferRef.current) bufferRef.current = document.createElement("canvas");
    scaleOnto(ctx, image, bufferRef.current);
  }, [frames]);

  return <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} style={{ width: "100%" }} />;
}
