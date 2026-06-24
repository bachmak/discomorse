import { useEffect } from "react";
import { useStore, MAX_SCOPE_SAMPLES } from "../store";
import { demoScopeChunk, demoSignalLength } from "../fixtures/oscilloscope";
import { demoWaterfallFrame } from "../fixtures/waterfall";

const CHUNK_SAMPLES = 12;

export function useDemoSignal(enabled: boolean): void {
  const appendScope = useStore((s) => s.appendScope);
  const setScope = useStore((s) => s.setScope);
  const pushWaterfall = useStore((s) => s.pushWaterfall);

  useEffect(() => {
    if (!enabled) return;
    setScope(demoScopeChunk(0, MAX_SCOPE_SAMPLES));
    let cursor = MAX_SCOPE_SAMPLES;
    let handle = 0;

    const tick = (): void => {
      appendScope(demoScopeChunk(cursor, CHUNK_SAMPLES));
      pushWaterfall(demoWaterfallFrame(cursor));
      cursor = (cursor + CHUNK_SAMPLES) % demoSignalLength;
      handle = requestAnimationFrame(tick);
    };

    handle = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(handle);
  }, [enabled, appendScope, setScope, pushWaterfall]);
}
