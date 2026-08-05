import type { ServerMessage } from "../types/ws";
import { NdjsonStream } from "./ndjsonStream";

// The wire types are generated from the backend's own models, so a line that
// gets this far is an envelope by construction.
export function parseEnvelope(line: string): ServerMessage {
  return JSON.parse(line) as ServerMessage;
}

// A decoder's NDJSON body, one parsed envelope at a time.
export class EnvelopeStream {
  constructor(private readonly body: ReadableStream<Uint8Array>) {}

  async *envelopes(): AsyncGenerator<ServerMessage> {
    for await (const line of new NdjsonStream(this.body).lines()) yield parseEnvelope(line);
  }
}
