import type { ToneSpectrumMessage } from "../types/ws";

export interface MessageSink {
  pushSpectrum(frame: ToneSpectrumMessage): void;
  pushKeying(on: boolean): void;
  appendMorseElement(notation: string): void;
  appendCorrectedText(text: string): void;
}
