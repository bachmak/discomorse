import { useEffect } from "react";
import { useStore, MAX_SCOPE_SAMPLES } from "../store";
import { demoScopeChunk, demoSignalLength } from "../fixtures/oscilloscope";
import { demoWaterfallFrame } from "../fixtures/waterfall";
import { demoSpectrumFrame } from "../fixtures/spectrum";
import type { FFTMessage } from "../types/ws";

const CHUNK_SAMPLES = 12;

function demoFftFrame(cursor: number): FFTMessage {
  return { type: "fft", data: demoSpectrumFrame(cursor), ts: performance.now() };
}

export function useDemoSignal(enabled: boolean): void {
  const appendScope = useStore((s) => s.appendScope);
  const setScope = useStore((s) => s.setScope);
  const pushWaterfall = useStore((s) => s.pushWaterfall);
  const pushFFT = useStore((s) => s.pushFFT);

  useEffect(() => {
    if (!enabled) return;
    setScope(demoScopeChunk(0, MAX_SCOPE_SAMPLES));
    pushFFT(demoFftFrame(MAX_SCOPE_SAMPLES - 1));
    let cursor = MAX_SCOPE_SAMPLES;
    let handle = 0;

    const tick = (): void => {
      appendScope(demoScopeChunk(cursor, CHUNK_SAMPLES));
      pushWaterfall(demoWaterfallFrame(cursor));
      pushFFT(demoFftFrame(cursor));
      cursor = (cursor + CHUNK_SAMPLES) % demoSignalLength;
      handle = requestAnimationFrame(tick);
    };

    handle = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(handle);
  }, [enabled, appendScope, setScope, pushWaterfall, pushFFT]);
}
