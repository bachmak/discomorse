import type { FFTMessage, WaterfallMessage } from "../types/ws";

export interface MessageSink {
  pushWaterfall(frame: WaterfallMessage): void;
  pushFFT(frame: FFTMessage): void;
  appendScope(samples: number[]): void;
  setScope(samples: number[]): void;
  appendMorse(notation: string): void;
  appendText(text: string): void;
}
