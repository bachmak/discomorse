export interface FrameSink {
  onFrame(): void;
}

export class Ticker {
  private running = false;
  private id = 0;

  constructor(private readonly sink: FrameSink) {}

  start(): void {
    if (this.running) return;
    this.running = true;
    this.id = requestAnimationFrame(this.loop);
  }

  stop(): void {
    this.running = false;
    cancelAnimationFrame(this.id);
  }

  private loop = (): void => {
    if (!this.running) return;
    this.sink.onFrame();
    if (this.running) this.id = requestAnimationFrame(this.loop);
  };
}
