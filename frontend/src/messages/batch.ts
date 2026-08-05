import { CappedList } from "../signals/cappedList";
import { MAX_KEYING_SAMPLES, SPECTRUM_HISTORY_FRAMES } from "../signals/history";
import type { ToneSpectrumMessage } from "../types/ws";
import type { MessageSink } from "./sink";

export interface Batch {
  spectrums: ToneSpectrumMessage[];
  keying: boolean[];
  morse: string;
  symbols: string;
  text: string;
}

export interface BatchTarget {
  apply(batch: Batch): void;
}

// Everything that arrives between two commits, held in one place. What the
// history would drop anyway is dropped here rather than carried any further.
export class BatchingSink implements MessageSink {
  private readonly spectrums = new CappedList<ToneSpectrumMessage>(SPECTRUM_HISTORY_FRAMES);
  private readonly keying = new CappedList<boolean>(MAX_KEYING_SAMPLES);
  private morse = "";
  private symbols = "";
  private text = "";

  get empty(): boolean {
    return this.signalCount + this.textLength === 0;
  }

  pushSpectrum(frame: ToneSpectrumMessage): void {
    this.spectrums.add(frame);
  }

  pushKeying(on: boolean): void {
    this.keying.add(on);
  }

  appendMorseElement(notation: string): void {
    this.morse += notation;
  }

  appendDecodedSymbol(symbol: string): void {
    this.symbols += symbol;
  }

  appendCorrectedText(text: string): void {
    this.text += text;
  }

  take(): Batch {
    const batch: Batch = {
      spectrums: this.spectrums.take(),
      keying: this.keying.take(),
      morse: this.morse,
      symbols: this.symbols,
      text: this.text,
    };
    this.morse = "";
    this.symbols = "";
    this.text = "";
    return batch;
  }

  private get signalCount(): number {
    return this.spectrums.size + this.keying.size;
  }

  private get textLength(): number {
    return this.morse.length + this.symbols.length + this.text.length;
  }
}
