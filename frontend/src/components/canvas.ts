import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

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

export function prepareContext(
  canvas: HTMLCanvasElement,
  size: CanvasSize,
): CanvasRenderingContext2D | null {
  const ratio = window.devicePixelRatio || 1;
  canvas.width = size.width * ratio;
  canvas.height = size.height * ratio;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return ctx;
}
