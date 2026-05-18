import { useEffect, useRef } from "react";
import { useStore } from "../store";

export function FFTSpectrum() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frame = useStore((s) => s.fftFrame);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !frame) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const barW = w / frame.data.length;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#00cccc";
    frame.data.forEach((mag, i) => {
      const barH = mag * h;
      ctx.fillRect(i * barW, h - barH, barW - 1, barH);
    });
  }, [frame]);

  return <canvas ref={canvasRef} width={800} height={150} style={{ width: "100%" }} />;
}
