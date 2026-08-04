/**
 * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.messages).
 * Do not edit by hand — run `npm run gen:ws-types`.
 */
export type ChannelName =
  | "spectrums"
  | "limited_spectrums"
  | "carrier_samples"
  | "noise_samples"
  | "raw_tones"
  | "debounced_tones"
  | "morse_elements"
  | "decoded_symbols"
  | "corrected_text";
export type OutboundMessage =
  | ToneSpectrumMessage
  | ToneMessage
  | CarrierSampleMessage
  | NoiseSampleMessage
  | DigitalToneMessage
  | TextMessage;

export interface ServerMessage {
  channel: ChannelName;
  payload: OutboundMessage;
}
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
export interface TextMessage {
  data: string;
  type: "text";
}
export interface MicHandshakeMessage {
  sample_rate: number;
  subscription: SubscriptionMessage;
}
export interface SubscriptionMessage {
  channels: ChannelName[];
}
