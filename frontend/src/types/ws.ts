export interface WaterfallMessage {
  type: "waterfall";
  data: number[];
  ts: number;
}

export interface FFTMessage {
  type: "fft";
  data: number[];
  ts: number;
}

export interface OscilloscopeMessage {
  type: "oscilloscope";
  data: number[];
  mode?: "append" | "replace";
  ts: number;
}

export interface TextMessage {
  type: "text";
  data: string;
}

export type ServerMessage =
  | WaterfallMessage
  | FFTMessage
  | OscilloscopeMessage
  | TextMessage;
