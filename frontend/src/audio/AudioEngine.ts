import { AudioFileDecoder } from "./AudioFileDecoder";
import { AudioGraph } from "./AudioGraph";
import { BufferPlayback } from "./BufferPlayback";
import { Listeners, type Listener, type Unsubscribe } from "./Listeners";
import { Ticker, type FrameSink } from "./Ticker";
import { idleTransport, type TransportState } from "./TransportState";

export class AudioEngine implements FrameSink {
  private readonly graph = new AudioGraph();
  private readonly decoder = new AudioFileDecoder(this.graph);
  private readonly listeners = new Listeners();
  private readonly ticker = new Ticker(this);
  private playback: BufferPlayback | null = null;
  private fileName: string | null = null;
  private state: TransportState = idleTransport();

  get analyser(): AnalyserNode {
    return this.graph.analyser;
  }

  subscribe = (listener: Listener): Unsubscribe => this.listeners.add(listener);

  getState = (): TransportState => this.state;

  async load(file: File): Promise<void> {
    const buffer = await this.decoder.decode(file);
    this.ticker.stop();
    this.playback = new BufferPlayback(this.graph, buffer);
    this.fileName = file.name;
    this.publish();
  }

  async play(): Promise<void> {
    if (!this.playback) return;
    await this.graph.resume();
    this.playback.start();
    this.ticker.start();
    this.publish();
  }

  pause(): void {
    if (!this.playback) return;
    this.playback.pause();
    this.ticker.stop();
    this.publish();
  }

  async toggle(): Promise<void> {
    if (this.playback?.playing) return this.pause();
    await this.play();
  }

  seek(seconds: number): void {
    this.playback?.seek(seconds);
    this.publish();
  }

  onFrame(): void {
    if (this.playback?.atEnd()) return this.pause();
    this.publish();
  }

  private publish(): void {
    this.state = this.snapshot();
    this.listeners.notify();
  }

  private snapshot(): TransportState {
    if (!this.playback) return idleTransport();
    return {
      fileName: this.fileName,
      playing: this.playback.playing,
      currentTime: this.playback.currentTime,
      duration: this.playback.duration,
    };
  }
}
