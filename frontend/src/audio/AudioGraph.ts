export class AudioGraph {
  private readonly context: AudioContext;
  private readonly analyserNode: AnalyserNode;

  constructor() {
    this.context = new AudioContext();
    this.analyserNode = this.context.createAnalyser();
    this.analyserNode.fftSize = 2048;
    this.analyserNode.connect(this.context.destination);
  }

  get analyser(): AnalyserNode {
    return this.analyserNode;
  }

  get now(): number {
    return this.context.currentTime;
  }

  async resume(): Promise<void> {
    await this.context.resume();
  }

  async decode(data: ArrayBuffer): Promise<AudioBuffer> {
    return this.context.decodeAudioData(data);
  }

  connectSource(buffer: AudioBuffer): AudioBufferSourceNode {
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    source.connect(this.analyserNode);
    return source;
  }
}
