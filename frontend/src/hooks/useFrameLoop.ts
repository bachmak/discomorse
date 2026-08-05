import { useEffect, useRef } from "react";
import type { MutableRefObject } from "react";
import { AnimationFrameRate, FramePacer } from "../pacing/framePacer";

async function repaint(render: MutableRefObject<() => void>, signal: AbortSignal): Promise<void> {
  const pacer = new FramePacer(new AnimationFrameRate());
  while (!signal.aborted) {
    render.current();
    await pacer.next(signal);
  }
}

// A view of a stream draws on the screen's clock rather than the decoder's:
// every frame paints wherever the data has got to by then, so a burst of
// arrivals and a stall between them look the same from the outside.
export function useFrameLoop(render: () => void): void {
  const latest = useRef(render);
  latest.current = render;

  useEffect(() => {
    const frames = new AbortController();
    void repaint(latest, frames.signal);
    return () => frames.abort();
  }, []);
}
