import type {
  FFTMessage,
  MorseMessage,
  OscilloscopeMessage,
  ServerMessage,
  TextMessage,
  WaterfallMessage,
} from "../types/ws";
import type { MessageSink } from "./sink";

export type MessageType = ServerMessage["type"];

export interface MessageHandler<M extends ServerMessage> {
  handle(message: M, sink: MessageSink): void;
}

interface ScopeMode {
  write(samples: number[], sink: MessageSink): void;
}

class AppendScope implements ScopeMode {
  write(samples: number[], sink: MessageSink): void {
    sink.appendScope(samples);
  }
}

class ReplaceScope implements ScopeMode {
  write(samples: number[], sink: MessageSink): void {
    sink.setScope(samples);
  }
}

const SCOPE_MODES = {
  append: new AppendScope(),
  replace: new ReplaceScope(),
} satisfies Record<string, ScopeMode>;

const DEFAULT_SCOPE_MODE = "replace";

class WaterfallHandler implements MessageHandler<WaterfallMessage> {
  handle(message: WaterfallMessage, sink: MessageSink): void {
    sink.pushWaterfall(message);
  }
}

class FFTHandler implements MessageHandler<FFTMessage> {
  handle(message: FFTMessage, sink: MessageSink): void {
    sink.pushFFT(message);
  }
}

class OscilloscopeHandler implements MessageHandler<OscilloscopeMessage> {
  handle(message: OscilloscopeMessage, sink: MessageSink): void {
    SCOPE_MODES[message.mode ?? DEFAULT_SCOPE_MODE].write(message.data, sink);
  }
}

class MorseHandler implements MessageHandler<MorseMessage> {
  handle(message: MorseMessage, sink: MessageSink): void {
    sink.appendMorse(message.data);
  }
}

class TextHandler implements MessageHandler<TextMessage> {
  handle(message: TextMessage, sink: MessageSink): void {
    sink.appendText(message.data);
  }
}

type HandlerTable = {
  [T in MessageType]: MessageHandler<Extract<ServerMessage, { type: T }>>;
};

export const HANDLERS: HandlerTable = {
  waterfall: new WaterfallHandler(),
  fft: new FFTHandler(),
  oscilloscope: new OscilloscopeHandler(),
  morse: new MorseHandler(),
  text: new TextHandler(),
};
