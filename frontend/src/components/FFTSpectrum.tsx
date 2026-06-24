import { useEffect, useRef } from "react";
import { useStore } from "../store";
import { NYQUIST_HZ } from "../audioFormat";

const WIDTH = 900;
const HEIGHT = 160;
const AXIS_HEIGHT = 22;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;
const TICK_HZ = 1000;
const TRACE_COLOR = "#22d3ee";
const FILL_COLOR = "rgba(34, 211, 238, 0.22)";
const GUIDE_COLOR = "rgba(34, 211, 238, 0.16)";
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";
const LABEL_COLOR = "rgba(148, 163, 184, 0.9)";

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function hzLabel(hz: number): string {
  return hz === 0 ? "0" : `${hz / 1000}k`;
}

function drawTick(ctx: CanvasRenderingContext2D, hz: number): void {
  const x = (hz / NYQUIST_HZ) * WIDTH;
  ctx.beginPath();
  ctx.moveTo(x, 0);
  ctx.lineTo(x, PLOT_HEIGHT);
  ctx.stroke();
  ctx.fillText(hzLabel(hz), Math.min(WIDTH - 12, Math.max(12, x)), HEIGHT - 6);
}

function drawAxis(ctx: CanvasRenderingContext2D): void {
  ctx.strokeStyle = GUIDE_COLOR;
  ctx.fillStyle = LABEL_COLOR;
  ctx.lineWidth = 1;
  ctx.font = "11px ui-monospace, monospace";
  ctx.textAlign = "center";
  for (let hz = 0; hz <= NYQUIST_HZ; hz += TICK_HZ) drawTick(ctx, hz);
}

function drawSpectrum(ctx: CanvasRenderingContext2D, data: number[]): void {
  const denom = Math.max(1, data.length - 1);
  ctx.beginPath();
  ctx.moveTo(0, PLOT_HEIGHT);
  data.forEach((mag, i) => ctx.lineTo((i / denom) * WIDTH, PLOT_HEIGHT - clamp01(mag) * PLOT_HEIGHT));
  ctx.lineTo(WIDTH, PLOT_HEIGHT);
  ctx.closePath();
  ctx.fillStyle = FILL_COLOR;
  ctx.fill();
  ctx.strokeStyle = TRACE_COLOR;
  ctx.lineWidth = 1;
  ctx.stroke();
}

function drawHint(ctx: CanvasRenderingContext2D): void {
  ctx.fillStyle = HINT_COLOR;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", WIDTH / 2, PLOT_HEIGHT / 2);
}

export function FFTSpectrum() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frame = useStore((s) => s.fftFrame);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    drawAxis(ctx);
    if (frame && frame.data.length > 0) drawSpectrum(ctx, frame.data);
    else drawHint(ctx);
  }, [frame]);

  return <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} style={{ width: "100%" }} />;
}
