import { clamp01 } from "./numbers";
import type { ItemWindow, PlotBox } from "./window";

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

const HALF_COLUMN = 0.5;

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

function paintRow(image: ImageData, row: number, magnitudes: readonly number[]): void {
  for (let x = 0; x < image.width; x++) {
    const [r, g, b] = magnitudeColor(magnitudes[x] ?? 0);
    const offset = (row * image.width + x) * 4;
    image.data.set([r, g, b, 255], offset);
  }
}

function buildImage(rows: readonly (readonly number[])[]): ImageData | null {
  const width = rows.length > 0 ? rows[rows.length - 1].length : 0;
  if (width === 0) return null;
  const image = new ImageData(width, rows.length);
  rows.forEach((magnitudes, row) => paintRow(image, row, magnitudes));
  return image;
}

// A column is centred on its sample and the last sample sits at fraction 1, so
// the visible slice starts half a column past where the fraction alone lands.
function sourceEdge(fraction: number, columns: number): number {
  return fraction * (columns - 1) + HALF_COLUMN;
}

/** Paints one bitmap column per sample, then stretches the visible slice over the plot. */
export class Spectrogram {
  private readonly buffer = document.createElement("canvas");

  draw(
    ctx: CanvasRenderingContext2D,
    rows: readonly (readonly number[])[],
    visible: ItemWindow,
    box: PlotBox,
  ): void {
    const image = buildImage(rows);
    if (!image) return;
    this.load(image);
    const from = sourceEdge(visible.from, image.width);
    const to = sourceEdge(visible.to, image.width);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(this.buffer, from, 0, to - from, image.height, 0, 0, box.width, box.height);
  }

  private load(image: ImageData): void {
    this.buffer.width = image.width;
    this.buffer.height = image.height;
    this.buffer.getContext("2d")?.putImageData(image, 0, 0);
  }
}
