import type { RefObject } from "react";

interface ChartCanvasProps {
  canvasRef: RefObject<HTMLCanvasElement>;
  height: number;
  goLive: () => void;
}

export function ChartCanvas({ canvasRef, height, goLive }: ChartCanvasProps) {
  return <canvas ref={canvasRef} className="chart" style={{ height }} onDoubleClick={goLive} />;
}
