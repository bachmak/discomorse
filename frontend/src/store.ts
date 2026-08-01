import { create } from "zustand";
import { SCOPE_RATE_HZ } from "./audioFormat";
import type { WaterfallMessage, FFTMessage } from "./types/ws";

// History deep enough to scroll back through, not just the visible window.
const WATERFALL_HISTORY_FRAMES = 2000;
const SCOPE_HISTORY_SECONDS = 30;
export const MAX_SCOPE_SAMPLES = SCOPE_HISTORY_SECONDS * SCOPE_RATE_HZ;

interface Signals {
  waterfallFrames: WaterfallMessage[];
  fftFrame: FFTMessage | null;
  scopeSamples: number[];
}

interface Decoded {
  decodedMorse: string;
  decodedText: string;
}

interface State extends Signals, Decoded {
  slowMode: boolean;
  pushWaterfall: (frame: WaterfallMessage) => void;
  pushFFT: (frame: FFTMessage) => void;
  appendScope: (samples: number[]) => void;
  setScope: (samples: number[]) => void;
  appendMorse: (notation: string) => void;
  appendText: (text: string) => void;
  clearDecoded: () => void;
  reset: () => void;
  setSlowMode: (on: boolean) => void;
}

const NO_SIGNALS: Signals = { waterfallFrames: [], fftFrame: null, scopeSamples: [] };
const NO_DECODED: Decoded = { decodedMorse: "", decodedText: "" };

export const useStore = create<State>((set) => ({
  ...NO_SIGNALS,
  ...NO_DECODED,
  slowMode: false,

  pushWaterfall: (frame) =>
    set((s) => ({
      waterfallFrames: [...s.waterfallFrames.slice(-WATERFALL_HISTORY_FRAMES + 1), frame],
    })),

  pushFFT: (frame) => set({ fftFrame: frame }),

  appendScope: (samples) =>
    set((s) => ({ scopeSamples: s.scopeSamples.concat(samples).slice(-MAX_SCOPE_SAMPLES) })),

  setScope: (samples) => set({ scopeSamples: samples }),

  appendMorse: (notation) => set((s) => ({ decodedMorse: s.decodedMorse + notation })),

  appendText: (text) => set((s) => ({ decodedText: s.decodedText + text })),

  clearDecoded: () => set({ ...NO_DECODED }),

  reset: () => set({ ...NO_SIGNALS, ...NO_DECODED }),

  setSlowMode: (on) => set({ slowMode: on }),
}));
