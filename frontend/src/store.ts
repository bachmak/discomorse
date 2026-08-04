import { create } from "zustand";
import { HOP_RATE_HZ } from "./audioFormat";
import type { ToneSpectrumMessage } from "./types/ws";

// History deep enough to scroll back through, not just the visible window.
const SPECTRUM_HISTORY_FRAMES = 2000;
const KEYING_HISTORY_SECONDS = 30;
export const MAX_KEYING_SAMPLES = KEYING_HISTORY_SECONDS * HOP_RATE_HZ;

const KEY_DOWN = 1;
const KEY_UP = 0;

interface Signals {
  spectrumFrames: ToneSpectrumMessage[];
  keyingLevels: number[];
}

interface Decoded {
  decodedMorse: string;
  decodedSymbols: string;
  correctedText: string;
}

interface State extends Signals, Decoded {
  slowMode: boolean;
  pushSpectrum: (frame: ToneSpectrumMessage) => void;
  pushKeying: (on: boolean) => void;
  appendMorseElement: (notation: string) => void;
  appendDecodedSymbol: (symbol: string) => void;
  appendCorrectedText: (text: string) => void;
  clearDecoded: () => void;
  reset: () => void;
  setSlowMode: (on: boolean) => void;
}

const NO_SIGNALS: Signals = { spectrumFrames: [], keyingLevels: [] };
const NO_DECODED: Decoded = { decodedMorse: "", decodedSymbols: "", correctedText: "" };

export const useStore = create<State>((set) => ({
  ...NO_SIGNALS,
  ...NO_DECODED,
  slowMode: false,

  pushSpectrum: (frame) =>
    set((s) => ({
      spectrumFrames: [...s.spectrumFrames.slice(-SPECTRUM_HISTORY_FRAMES + 1), frame],
    })),

  pushKeying: (on) =>
    set((s) => ({
      keyingLevels: [...s.keyingLevels.slice(-MAX_KEYING_SAMPLES + 1), on ? KEY_DOWN : KEY_UP],
    })),

  appendMorseElement: (notation) => set((s) => ({ decodedMorse: s.decodedMorse + notation })),

  appendDecodedSymbol: (symbol) => set((s) => ({ decodedSymbols: s.decodedSymbols + symbol })),

  appendCorrectedText: (text) => set((s) => ({ correctedText: s.correctedText + text })),

  clearDecoded: () => set({ ...NO_DECODED }),

  reset: () => set({ ...NO_SIGNALS, ...NO_DECODED }),

  setSlowMode: (on) => set({ slowMode: on }),
}));
