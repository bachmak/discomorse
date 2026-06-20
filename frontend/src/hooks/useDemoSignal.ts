import { useEffect } from "react";
import { useStore } from "../store";
import { demoOscilloscopeFrames } from "../fixtures/oscilloscope";

const FRAME_INTERVAL_MS = 1000 / 30;

export function useDemoSignal(enabled: boolean): void {
  const pushOscilloscope = useStore((s) => s.pushOscilloscope);

  useEffect(() => {
    if (!enabled) return;
    const frames = demoOscilloscopeFrames();
    let handle = 0;
    let index = 0;
    let lastAt = 0;

    const tick = (now: number): void => {
      if (now - lastAt >= FRAME_INTERVAL_MS) {
        pushOscilloscope(frames[index % frames.length]);
        index += 1;
        lastAt = now;
      }
      handle = requestAnimationFrame(tick);
    };

    handle = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(handle);
  }, [enabled, pushOscilloscope]);
}
