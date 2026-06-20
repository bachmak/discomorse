import { useEffect, useRef } from "react";
import { useStore } from "../store";

const WIDTH = 900;
const HEIGHT = 160;
const MID = HEIGHT / 2;
const AMPLITUDE = MID * 0.9;
const TRACE_COLOR = "#22d3ee";
const FILL_COLOR = "rgba(34, 211, 238, 0.22)";
const GUIDE_COLOR = "rgba(34, 211, 238, 0.16)";
const HINT_COLOR = "rgba(148, 163, 184, 0.75)";

function drawBaseline(ctx: CanvasRenderingContext2D): void {
  ctx.strokeStyle = GUIDE_COLOR;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, MID);
  ctx.lineTo(WIDTH, MID);
  ctx.stroke();
}

function columnPeak(samples: number[], from: number, to: number): number {
  const start = Math.floor(from);
  const end = Math.min(samples.length, Math.max(start + 1, Math.floor(to)));
  let peak = 0;
  for (let i = start; i < end; i++) {
    const magnitude = Math.abs(samples[i]);
    if (magnitude > peak) peak = magnitude;
  }
  return peak;
}

function drawWaveform(ctx: CanvasRenderingContext2D, samples: number[]): void {
  const perColumn = samples.length / WIDTH;
  const peaks = Array.from({ length: WIDTH }, (_u, x) =>
    columnPeak(samples, x * perColumn, (x + 1) * perColumn),
  );
  ctx.beginPath();
  peaks.forEach((peak, x) => ctx.lineTo(x, MID - peak * AMPLITUDE));
  for (let x = WIDTH - 1; x >= 0; x--) ctx.lineTo(x, MID + peaks[x] * AMPLITUDE);
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
  ctx.fillText("Waiting for signal…", WIDTH / 2, MID - 8);
}

export function Oscilloscope() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const samples = useStore((s) => s.scopeSamples);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    drawBaseline(ctx);
    if (samples.length > 0) drawWaveform(ctx, samples);
    else drawHint(ctx);
  }, [samples]);

  return <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} style={{ width: "100%" }} />;
}
