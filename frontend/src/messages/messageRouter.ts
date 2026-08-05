import type { OutboundMessage, ServerMessage } from "../types/ws";
import { parseEnvelope } from "./envelope";
import { HANDLERS, type MessageHandler } from "./handlers";
import type { MessageSink } from "./sink";

export class MessageRouter {
  constructor(private readonly sink: MessageSink) {}

  route(envelope: string): void {
    this.deliver(parseEnvelope(envelope));
  }

  // The channel is what a message is routed by: several stages send the same
  // payload shape, so the payload alone no longer says where it belongs.
  deliver({ channel, payload }: ServerMessage): void {
    this.handlerFor(channel).handle(payload, this.sink);
  }

  // The table is keyed by the very channel the envelope names, but TS cannot
  // correlate an indexed handler with the union-typed payload, so we narrow.
  private handlerFor(channel: ServerMessage["channel"]): MessageHandler<OutboundMessage> {
    return HANDLERS[channel] as MessageHandler<OutboundMessage>;
  }
}
