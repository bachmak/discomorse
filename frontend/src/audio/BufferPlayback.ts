import type { AudioGraph } from "./AudioGraph";

export class BufferPlayback {
  private offset = 0;
  private startedAt = 0;
  private source: AudioBufferSourceNode | null = null;

  constructor(
    private readonly graph: AudioGraph,
    private readonly buffer: AudioBuffer,
  ) {}

  get duration(): number {
    return this.buffer.duration;
  }

  get playing(): boolean {
    return this.source !== null;
  }

  get currentTime(): number {
    const elapsed = this.playing ? this.graph.now - this.startedAt : 0;
    return Math.min(this.offset + elapsed, this.duration);
  }

  atEnd(): boolean {
    return this.currentTime >= this.duration;
  }

  start(): void {
    if (this.playing) return;
    if (this.atEnd()) this.offset = 0;
    this.source = this.graph.connectSource(this.buffer);
    this.startedAt = this.graph.now;
    this.source.start(0, this.offset);
  }

  pause(): void {
    this.offset = this.currentTime;
    this.teardown();
  }

  seek(seconds: number): void {
    const resume = this.playing;
    this.teardown();
    this.offset = Math.min(Math.max(seconds, 0), this.duration);
    if (resume) this.start();
  }

  private teardown(): void {
    if (!this.source) return;
    this.source.stop();
    this.source.disconnect();
    this.source = null;
  }
}
