import type {
  DigitalToneMessage,
  MorseElementMessage,
  OutboundMessage,
  ToneSpectrumMessage,
  TranscriptionMessage,
} from "../types/ws";
import type { MessageSink } from "./sink";

export type MessageType = OutboundMessage["type"];

export interface MessageHandler<M extends OutboundMessage> {
  handle(message: M, sink: MessageSink): void;
}

class ToneSpectrumHandler implements MessageHandler<ToneSpectrumMessage> {
  handle(message: ToneSpectrumMessage, sink: MessageSink): void {
    sink.pushSpectrum(message);
  }
}

class DigitalToneHandler implements MessageHandler<DigitalToneMessage> {
  handle(message: DigitalToneMessage, sink: MessageSink): void {
    sink.pushKeying(message.on);
  }
}

class MorseElementHandler implements MessageHandler<MorseElementMessage> {
  handle(message: MorseElementMessage, sink: MessageSink): void {
    sink.appendMorseElement(message.data);
  }
}

class TranscriptionHandler implements MessageHandler<TranscriptionMessage> {
  handle(message: TranscriptionMessage, sink: MessageSink): void {
    sink.appendTranscription(message.data);
  }
}

// Diagnostic streams the backend can be configured to send but no chart reads.
class IgnoredHandler implements MessageHandler<OutboundMessage> {
  handle(): void {}
}

const IGNORED = new IgnoredHandler();

type HandlerTable = {
  [T in MessageType]: MessageHandler<Extract<OutboundMessage, { type: T }>>;
};

export const HANDLERS: HandlerTable = {
  tone_spectrum: new ToneSpectrumHandler(),
  digital_tone: new DigitalToneHandler(),
  morse_element: new MorseElementHandler(),
  transcription: new TranscriptionHandler(),
  tone: IGNORED,
  carrier_sample: IGNORED,
  noise_sample: IGNORED,
};
