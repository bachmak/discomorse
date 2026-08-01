import type { ServerMessage } from "../types/ws";
import { HANDLERS, type MessageHandler } from "./handlers";
import type { MessageSink } from "./sink";

export class MessageRouter {
  constructor(private readonly sink: MessageSink) {}

  route(payload: string): void {
    this.dispatch(JSON.parse(payload) as ServerMessage);
  }

  private dispatch<M extends ServerMessage>(message: M): void {
    // The table is keyed by the very discriminant the message carries, but TS
    // cannot correlate an indexed handler with a generic message, so we narrow.
    const handler = HANDLERS[message.type] as MessageHandler<M>;
    handler.handle(message, this.sink);
  }
}
