import { useEffect, useRef } from "react";
import { useStore } from "../store";

export function Waterfall() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frames = useStore((s) => s.waterfallFrames);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || frames.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const rowH = h / frames.length;

    ctx.clearRect(0, 0, w, h);
    frames.forEach((frame, rowIdx) => {
      frame.data.forEach((mag, binIdx) => {
        const x = Math.floor((binIdx / frame.data.length) * w);
        const intensity = Math.min(255, Math.floor(mag * 255));
        ctx.fillStyle = `rgb(0,${intensity},${intensity})`;
        ctx.fillRect(x, rowIdx * rowH, Math.ceil(w / frame.data.length), rowH);
      });
    });
  }, [frames]);

  return <canvas ref={canvasRef} width={800} height={300} style={{ width: "100%" }} />;
}
