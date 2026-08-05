import { BatchingSink, type BatchTarget } from "../messages/batch";
import type { MessageSink } from "../messages/sink";
import { AnimationFrameRate, FramePacer } from "./framePacer";

// A decoder emits a spectrum and a key reading every hop — hundreds per second,
// an order of magnitude more often than the screen is repainted. Committing
// each one separately redrew every chart for a slice of a pixel and starved the
// main thread, so the charts advanced in lurches. Buffering the messages and
// committing them one animation frame at a time lets them move at paint rate.
export class PacedIngest {
  private readonly buffer = new BatchingSink();
  private readonly pacer = new FramePacer(new AnimationFrameRate());
  private readonly frames = new AbortController();

  constructor(private readonly target: BatchTarget) {}

  get sink(): MessageSink {
    return this.buffer;
  }

  async run(): Promise<void> {
    const { signal } = this.frames;
    while (!signal.aborted) {
      this.flush();
      await this.pacer.next(signal);
    }
  }

  flush(): void {
    if (!this.buffer.empty) this.target.apply(this.buffer.take());
  }

  stop(): void {
    this.frames.abort();
  }
}
