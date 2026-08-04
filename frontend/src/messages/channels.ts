import type {
  CarrierSampleMessage,
  DigitalToneMessage,
  NoiseSampleMessage,
  TextMessage,
  ToneSpectrumMessage,
} from "../types/ws";

// Which payload shape every channel carries. The wire schema only types a
// payload as the whole union, and the stages that spell morse, decode symbols
// and correct text all share the text shape, so the channel an envelope names
// is the only thing that says which stage a message came from.
export interface ChannelPayload {
  spectrums: ToneSpectrumMessage;
  limited_spectrums: ToneSpectrumMessage;
  carrier_samples: CarrierSampleMessage;
  noise_samples: NoiseSampleMessage;
  raw_tones: DigitalToneMessage;
  debounced_tones: DigitalToneMessage;
  morse_elements: TextMessage;
  decoded_symbols: TextMessage;
  corrected_text: TextMessage;
}
