/**
 * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.messages).
 * Do not edit by hand — run `npm run gen:ws-types`.
 */
export type ServerMessage =
  | ToneSpectrumMessage
  | ToneMessage
  | CarrierSampleMessage
  | NoiseSampleMessage
  | DigitalToneMessage
  | MorseElementMessage
  | TranscriptionMessage;

export interface ToneSpectrumMessage {
  data: number[];
  ts: number;
  type: "tone_spectrum";
}
export interface ToneMessage {
  frequency: number;
  magnitude: number;
  ts: number;
  type: "tone";
}
export interface CarrierSampleMessage {
  frequency: number;
  is_locked: boolean;
  magnitude: number;
  ts: number;
  type: "carrier_sample";
}
export interface NoiseSampleMessage {
  magnitude: number;
  ts: number;
  type: "noise_sample";
}
export interface DigitalToneMessage {
  on: boolean;
  ts: number;
  type: "digital_tone";
}
export interface MorseElementMessage {
  data: string;
  type: "morse_element";
}
export interface TranscriptionMessage {
  data: string;
  type: "transcription";
}

export interface MicHandshakeMessage {
  sample_rate: number;
}
