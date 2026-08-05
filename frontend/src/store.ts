import { create } from "zustand";
import type { Batch } from "./messages/batch";
import { SPECTRUM_HISTORY_FRAMES, appendCapped } from "./signals/history";
import { KeyingHistory } from "./signals/keyingHistory";
import { NO_LINES, type DecodedLines } from "./text/decodedLines";
import type { ToneSpectrumMessage } from "./types/ws";

interface Signals {
  spectrumFrames: ToneSpectrumMessage[];
  keying: KeyingHistory;
}

interface Decoded {
  decoded: DecodedLines;
}

interface State extends Signals, Decoded {
  slowMode: boolean;
  apply: (batch: Batch) => void;
  clearDecoded: () => void;
  reset: () => void;
  setSlowMode: (on: boolean) => void;
}

const NO_SIGNALS: Signals = { spectrumFrames: [], keying: KeyingHistory.empty() };
const NO_DECODED: Decoded = { decoded: NO_LINES };

function appended(current: DecodedLines, batch: Batch): DecodedLines {
  return {
    morse: current.morse + batch.morse,
    symbols: current.symbols + batch.symbols,
    text: current.text + batch.text,
  };
}

function grown(current: Signals & Decoded, batch: Batch): Signals & Decoded {
  return {
    spectrumFrames: appendCapped(current.spectrumFrames, batch.spectrums, SPECTRUM_HISTORY_FRAMES),
    keying: current.keying.grownBy(batch.keying),
    decoded: appended(current.decoded, batch),
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
