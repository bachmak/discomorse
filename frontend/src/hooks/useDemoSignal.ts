import { useEffect } from "react";
import { useStore } from "../store";
import { demoKeyingOn } from "../fixtures/keying";
import { demoSpectrumMessage } from "../fixtures/spectrum";
import type { MessageSink } from "../messages/sink";
import { storeIngest } from "../pacing/storeIngest";
import { FramePacer, type FrameRate } from "../pacing/framePacer";

// One step is one hop of the backend's streams: a spectrum and a key reading.
// A dozen of them per animation frame runs the fixture at roughly live speed.
const STEPS_PER_FRAME = 12;
const FAST_FRAME_MS = 0;
const SLOW_FRAME_MS = 120;

class SlowAwareFrameRate implements FrameRate {
  currentMs(): number {
    return useStore.getState().slowMode ? SLOW_FRAME_MS : FAST_FRAME_MS;
  }
}

function emitStep(cursor: number, sink: MessageSink): void {
  sink.pushSpectrum(demoSpectrumMessage(cursor));
  sink.pushKeying(demoKeyingOn(cursor));
}

function emitFrame(frame: number, sink: MessageSink): void {
  const first = frame * STEPS_PER_FRAME;
  for (let step = 0; step < STEPS_PER_FRAME; step++) emitStep(first + step, sink);
}

async function streamDemo(signal: AbortSignal, sink: MessageSink): Promise<void> {
  const pacer = new FramePacer(new SlowAwareFrameRate());
  for await (const frame of pacer.frames(signal)) emitFrame(frame, sink);
}

export function useDemoSignal(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const ingest = storeIngest();
    void ingest.run();
    void streamDemo(controller.signal, ingest.sink);
    return () => {
      controller.abort();
      ingest.stop();
    };
  }, [enabled]);
}
