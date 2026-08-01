import { create } from "zustand";
import type { WaterfallMessage, FFTMessage } from "./types/ws";

const MAX_WATERFALL_FRAMES = 200;
export const MAX_SCOPE_SAMPLES = 1024;

interface State {
  waterfallFrames: WaterfallMessage[];
  fftFrame: FFTMessage | null;
  scopeSamples: number[];
  decodedMorse: string;
  decodedText: string;
  slowMode: boolean;
  pushWaterfall: (frame: WaterfallMessage) => void;
  pushFFT: (frame: FFTMessage) => void;
  appendScope: (samples: number[]) => void;
  setScope: (samples: number[]) => void;
  appendMorse: (notation: string) => void;
  appendText: (text: string) => void;
  clearDecoded: () => void;
  setSlowMode: (on: boolean) => void;
}

export const useStore = create<State>((set) => ({
  waterfallFrames: [],
  fftFrame: null,
  scopeSamples: [],
  decodedMorse: "",
  decodedText: "",
  slowMode: false,

  pushWaterfall: (frame) =>
    set((s) => ({
      waterfallFrames: [...s.waterfallFrames.slice(-MAX_WATERFALL_FRAMES + 1), frame],
    })),

  pushFFT: (frame) => set({ fftFrame: frame }),

  appendScope: (samples) =>
    set((s) => ({ scopeSamples: [...s.scopeSamples, ...samples].slice(-MAX_SCOPE_SAMPLES) })),

  setScope: (samples) => set({ scopeSamples: samples }),

  appendMorse: (notation) => set((s) => ({ decodedMorse: s.decodedMorse + notation })),

  appendText: (text) => set((s) => ({ decodedText: s.decodedText + text })),

  clearDecoded: () => set({ decodedMorse: "", decodedText: "" }),

  setSlowMode: (on) => set({ slowMode: on }),
}));
