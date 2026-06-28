import { useEffect } from "react";
import { useStore, MAX_SCOPE_SAMPLES } from "../store";
import { demoScopeChunk, demoSignalLength } from "../fixtures/oscilloscope";
import { demoWaterfallFrame } from "../fixtures/waterfall";
import { demoSpectrumFrame } from "../fixtures/spectrum";
import type { FFTMessage, WaterfallMessage } from "../types/ws";
import { FramePacer, type FrameRate } from "../pacing/framePacer";

const CHUNK_SAMPLES = 12;
const FAST_FRAME_MS = 0;
const SLOW_FRAME_MS = 120;

interface DemoSink {
  appendScope: (samples: number[]) => void;
  setScope: (samples: number[]) => void;
  pushWaterfall: (frame: WaterfallMessage) => void;
  pushFFT: (frame: FFTMessage) => void;
}

class SlowAwareFrameRate implements FrameRate {
  currentMs(): number {
    return useStore.getState().slowMode ? SLOW_FRAME_MS : FAST_FRAME_MS;
  }
}

function demoFftFrame(cursor: number): FFTMessage {
  return { type: "fft", data: demoSpectrumFrame(cursor), ts: performance.now() };
}

function scopeCursor(frame: number): number {
  return (MAX_SCOPE_SAMPLES + frame * CHUNK_SAMPLES) % demoSignalLength;
}

function seed(sink: DemoSink): void {
  sink.setScope(demoScopeChunk(0, MAX_SCOPE_SAMPLES));
  sink.pushFFT(demoFftFrame(MAX_SCOPE_SAMPLES - 1));
}

function emit(cursor: number, sink: DemoSink): void {
  sink.appendScope(demoScopeChunk(cursor, CHUNK_SAMPLES));
  sink.pushWaterfall(demoWaterfallFrame(cursor));
  sink.pushFFT(demoFftFrame(cursor));
}

async function streamDemo(signal: AbortSignal, sink: DemoSink): Promise<void> {
  seed(sink);
  const pacer = new FramePacer(new SlowAwareFrameRate());
  for await (const frame of pacer.frames(signal)) {
    emit(scopeCursor(frame), sink);
  }
}

function demoSink(): DemoSink {
  const { appendScope, setScope, pushWaterfall, pushFFT } = useStore.getState();
  return { appendScope, setScope, pushWaterfall, pushFFT };
}

export function useDemoSignal(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    void streamDemo(controller.signal, demoSink());
    return () => controller.abort();
  }, [enabled]);
}
