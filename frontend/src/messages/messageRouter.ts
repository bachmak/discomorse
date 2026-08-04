import type { OutboundMessage, ServerMessage } from "../types/ws";
import { HANDLERS, type MessageHandler } from "./handlers";
import type { MessageSink } from "./sink";

export class MessageRouter {
  constructor(private readonly sink: MessageSink) {}

  // The channel the payload came in on is dropped: the charts read one stream
  // per payload shape, which is what the default stream settings send.
  route(envelope: string): void {
    this.dispatch((JSON.parse(envelope) as ServerMessage).payload);
  }

  private dispatch<M extends OutboundMessage>(message: M): void {
    // The table is keyed by the very discriminant the message carries, but TS
    // cannot correlate an indexed handler with a generic message, so we narrow.
    const handler = HANDLERS[message.type] as MessageHandler<M>;
    handler.handle(message, this.sink);
  }
}
