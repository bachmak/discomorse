import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import type { ChartPalette } from "../charts/palette";
import type { ChartSurface } from "../charts/surface";

export interface CanvasSize {
  width: number;
  height: number;
}

export interface ResponsiveCanvas {
  ref: RefObject<HTMLCanvasElement>;
  size: CanvasSize;
}

export function useCanvasSize(height: number): ResponsiveCanvas {
  const ref = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  return { ref, size: { width, height } };
}

// Resizing a canvas throws its buffer away and allocates another, which a chart
// that redraws every frame cannot afford; one already the right size is cleared.
function resize(canvas: HTMLCanvasElement, size: CanvasSize, ratio: number): void {
  const width = Math.round(size.width * ratio);
  const height = Math.round(size.height * ratio);
  if (canvas.width === width && canvas.height === height) return;
  canvas.width = width;
  canvas.height = height;
}

export function prepareSurface(
  canvas: HTMLCanvasElement,
  size: CanvasSize,
  palette: ChartPalette,
): ChartSurface | null {
  const ratio = window.devicePixelRatio || 1;
  resize(canvas, size, ratio);
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, size.width, size.height);
  return { ctx, palette };
}
