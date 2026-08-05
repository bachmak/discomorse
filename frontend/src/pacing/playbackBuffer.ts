import type { OutboundMessage, ServerMessage } from "../types/ws";

interface Held {
  offset: number;
  message: ServerMessage;
}

// Messages waiting for their moment, in the order the decoder produced them and
// measured from the first of them, so a playhead may always start at zero.
export class PlaybackBuffer {
  private readonly held: Held[] = [];
  private origin: number | null = null;
  private offset = 0;

  get empty(): boolean {
    return this.held.length === 0;
  }

  // How far a playhead may run: nothing past this has arrived yet.
  get horizon(): number {
    return this.offset;
  }

  add(message: ServerMessage): void {
    this.held.push({ offset: this.offsetOf(message.payload), message });
  }

  until(position: number): ServerMessage[] {
    let due = 0;
    while (due < this.held.length && this.held[due].offset <= position) due++;
    return this.held.splice(0, due).map((held) => held.message);
  }

  // Text carries no timestamp of its own. It belongs to the audio moment of the
  // last stamped message ahead of it, which is what the decoder read to spell it.
  private offsetOf(payload: OutboundMessage): number {
    if (payload.type !== "text") {
      this.origin ??= payload.ts;
      this.offset = payload.ts - this.origin;
    }
    return this.offset;
  }
}
