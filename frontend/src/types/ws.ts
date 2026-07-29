/**
 * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.wire).
 * Do not edit by hand — run `npm run gen:ws-types`.
 */
export type ServerMessage = WaterfallMessage | FFTMessage | OscilloscopeMessage | TextMessage;

export interface WaterfallMessage {
  data: number[];
  ts: number;
  type?: "waterfall";
}
export interface FFTMessage {
  data: number[];
  ts: number;
  type?: "fft";
}
export interface OscilloscopeMessage {
  data: number[];
  mode?: ("append" | "replace") | null;
  ts: number;
  type?: "oscilloscope";
}
export interface TextMessage {
  data: string;
  type?: "text";
}

export interface MicHandshake {
  sample_rate: number;
}
