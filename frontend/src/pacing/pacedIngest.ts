import type { BatchTarget } from "../messages/batch";
import type { MessageSink } from "../messages/sink";
import { BatchCommit } from "./batchCommit";
import { AnimationFrameRate, FramePacer } from "./framePacer";

// A decoder emits a spectrum and a key reading every hop — hundreds per second,
// an order of magnitude more often than the screen is repainted. Committing
// each one separately redrew every chart for a slice of a pixel and starved the
// main thread, so the charts advanced in lurches. Buffering the messages and
// committing them one animation frame at a time lets them move at paint rate.
export class PacedIngest {
  private readonly commits: BatchCommit;
  private readonly pacer = new FramePacer(new AnimationFrameRate());
  private readonly frames = new AbortController();

  constructor(target: BatchTarget) {
    this.commits = new BatchCommit(target);
  }

  get sink(): MessageSink {
    return this.commits.sink;
  }

  async run(): Promise<void> {
    const { signal } = this.frames;
    while (!signal.aborted) {
      this.flush();
      await this.pacer.next(signal);
    }
  }

  flush(): void {
    this.commits.commit();
  }

  stop(): void {
    this.frames.abort();
  }
}
