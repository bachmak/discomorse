import type { RefObject } from "react";

interface ChartCanvasProps {
  canvasRef: RefObject<HTMLCanvasElement>;
  height: number;
  onReset: () => void;
}

export function ChartCanvas({ canvasRef, height, onReset }: ChartCanvasProps) {
  return <canvas ref={canvasRef} className="chart" style={{ height }} onDoubleClick={onReset} />;
}
