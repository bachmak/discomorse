import type { AudioGraph } from "./AudioGraph";

export class AudioFileDecoder {
  constructor(private readonly graph: AudioGraph) {}

  async decode(file: File): Promise<AudioBuffer> {
    const data = await file.arrayBuffer();
    return this.graph.decode(data);
  }
}
