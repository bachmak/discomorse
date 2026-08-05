import { create } from "zustand";
import type { Batch } from "./messages/batch";
import { MAX_KEYING_SAMPLES, SPECTRUM_HISTORY_FRAMES, appendCapped } from "./signals/history";
import type { ToneSpectrumMessage } from "./types/ws";

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
  apply: (batch: Batch) => void;
  clearDecoded: () => void;
  reset: () => void;
  setSlowMode: (on: boolean) => void;
}

const NO_SIGNALS: Signals = { spectrumFrames: [], keyingLevels: [] };
const NO_DECODED: Decoded = { decodedMorse: "", decodedSymbols: "", correctedText: "" };

function levels(keying: readonly boolean[]): number[] {
  return keying.map((on) => (on ? KEY_DOWN : KEY_UP));
}

function grown(current: Signals & Decoded, batch: Batch): Signals & Decoded {
  return {
    spectrumFrames: appendCapped(current.spectrumFrames, batch.spectrums, SPECTRUM_HISTORY_FRAMES),
    keyingLevels: appendCapped(current.keyingLevels, levels(batch.keying), MAX_KEYING_SAMPLES),
    decodedMorse: current.decodedMorse + batch.morse,
    decodedSymbols: current.decodedSymbols + batch.symbols,
    correctedText: current.correctedText + batch.text,
  };
}

export const useStore = create<State>((set) => ({
  ...NO_SIGNALS,
  ...NO_DECODED,
  slowMode: false,

  apply: (batch) => set((s) => grown(s, batch)),

  clearDecoded: () => set({ ...NO_DECODED }),

  reset: () => set({ ...NO_SIGNALS, ...NO_DECODED }),

  setSlowMode: (on) => set({ slowMode: on }),
}));
