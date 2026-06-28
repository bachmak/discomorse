import { create } from "zustand";
import type { WaterfallMessage, FFTMessage } from "./types/ws";

const MAX_WATERFALL_FRAMES = 200;
export const MAX_SCOPE_SAMPLES = 1024;

interface State {
  waterfallFrames: WaterfallMessage[];
  fftFrame: FFTMessage | null;
  scopeSamples: number[];
  decodedText: string;
  slowMode: boolean;
  pushWaterfall: (frame: WaterfallMessage) => void;
  pushFFT: (frame: FFTMessage) => void;
  appendScope: (samples: number[]) => void;
  setScope: (samples: number[]) => void;
  appendText: (text: string) => void;
  clearText: () => void;
  setSlowMode: (on: boolean) => void;
}

export const useStore = create<State>((set) => ({
  waterfallFrames: [],
  fftFrame: null,
  scopeSamples: [],
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

  appendText: (text) => set((s) => ({ decodedText: s.decodedText + text })),

  clearText: () => set({ decodedText: "" }),

  setSlowMode: (on) => set({ slowMode: on }),
}));
