import { create } from "zustand";
import type { WaterfallMessage, FFTMessage } from "./types/ws";

const MAX_WATERFALL_FRAMES = 200;

interface State {
  waterfallFrames: WaterfallMessage[];
  fftFrame: FFTMessage | null;
  decodedText: string;
  pushWaterfall: (frame: WaterfallMessage) => void;
  pushFFT: (frame: FFTMessage) => void;
  appendText: (text: string) => void;
  clearText: () => void;
}

export const useStore = create<State>((set) => ({
  waterfallFrames: [],
  fftFrame: null,
  decodedText: "",

  pushWaterfall: (frame) =>
    set((s) => ({
      waterfallFrames: [...s.waterfallFrames.slice(-MAX_WATERFALL_FRAMES + 1), frame],
    })),

  pushFFT: (frame) => set({ fftFrame: frame }),

  appendText: (text) => set((s) => ({ decodedText: s.decodedText + text })),

  clearText: () => set({ decodedText: "" }),
}));
