import type {
  ChannelName,
  DigitalToneMessage,
  OutboundMessage,
  TextMessage,
  ToneSpectrumMessage,
} from "../types/ws";
import type { ChannelPayload } from "./channels";
import type { MessageSink } from "./sink";

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

class MorseElementHandler implements MessageHandler<TextMessage> {
  handle(message: TextMessage, sink: MessageSink): void {
    sink.appendMorseElement(message.data);
  }
}

class DecodedSymbolHandler implements MessageHandler<TextMessage> {
  handle(message: TextMessage, sink: MessageSink): void {
    sink.appendDecodedSymbol(message.data);
  }
}

class CorrectedTextHandler implements MessageHandler<TextMessage> {
  handle(message: TextMessage, sink: MessageSink): void {
    sink.appendCorrectedText(message.data);
  }
}

// Diagnostic streams the backend can be configured to send but no view reads.
class IgnoredHandler implements MessageHandler<OutboundMessage> {
  handle(): void {}
}

const IGNORED = new IgnoredHandler();

// A channel the backend can name must have a handler, or this fails to compile.
type HandlerTable = {
  [C in ChannelName]: MessageHandler<ChannelPayload[C]>;
};

export const HANDLERS: HandlerTable = {
  spectrums: new ToneSpectrumHandler(),
  debounced_tones: new DigitalToneHandler(),
  morse_elements: new MorseElementHandler(),
  decoded_symbols: new DecodedSymbolHandler(),
  corrected_text: new CorrectedTextHandler(),
  limited_spectrums: IGNORED,
  carrier_samples: IGNORED,
  noise_samples: IGNORED,
  raw_tones: IGNORED,
};
