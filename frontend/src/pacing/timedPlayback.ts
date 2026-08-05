import type { BatchTarget } from "../messages/batch";
import { MessageRouter } from "../messages/messageRouter";
import type { ServerMessage } from "../types/ws";
import { BatchCommit } from "./batchCommit";
import { AnimationFrameRate, FramePacer } from "./framePacer";
import { PlaybackBuffer } from "./playbackBuffer";
import { PlaybackClock, type PlaybackRate } from "./playbackClock";

// Rendering a decoded file used to follow the network: everything that had
// arrived since the last frame was committed at once, so a link that delivers a
// round trip's worth in one go made the charts leap and then stand still. Here
// a message waits for the timestamp it carries, which turns a burst into a
// fuller buffer instead of a jump.
export class TimedPlayback {
  private readonly commits: BatchCommit;
  private readonly router: MessageRouter;
  private readonly buffer = new PlaybackBuffer();
  private readonly clock: PlaybackClock;
  private readonly pacer = new FramePacer(new AnimationFrameRate());
  private readonly frames = new AbortController();
  private arriving = true;

  constructor(target: BatchTarget, rate: PlaybackRate) {
    this.commits = new BatchCommit(target);
    this.router = new MessageRouter(this.commits.sink);
    this.clock = new PlaybackClock(rate);
  }

  // Resolves once the last message has been rendered, not once it arrived: the
  // buffer still holds everything that is not due yet when the stream ends.
  async play(envelopes: AsyncIterable<ServerMessage>): Promise<void> {
    await Promise.all([this.collect(envelopes), this.render()]);
  }

  stop(): void {
    this.frames.abort();
  }

  private async collect(envelopes: AsyncIterable<ServerMessage>): Promise<void> {
    try {
      for await (const envelope of envelopes) this.buffer.add(envelope);
    } finally {
      this.arriving = false;
    }
  }

  private async render(): Promise<void> {
    const { signal } = this.frames;
    while (!signal.aborted && this.unfinished) {
      this.releaseDue();
      this.commits.commit();
      await this.pacer.next(signal);
    }
  }

  private get unfinished(): boolean {
    return this.arriving || !this.buffer.empty;
  }

  private releaseDue(): void {
    const due = this.buffer.until(this.clock.advanceTo(this.buffer.horizon));
    for (const message of due) this.router.deliver(message);
  }
}
