import { PCM_ENCODER } from "./pcmEncoderName";

// The audio worklet scope is not in the DOM lib, so the two globals this
// processor stands on are declared here rather than pulled in.
declare abstract class AudioWorkletProcessor {
  readonly port: MessagePort;
}
declare function registerProcessor(
  name: string,
  processor: new () => AudioWorkletProcessor,
): void;

const CHUNK_SAMPLES = 2048;
const BYTES_PER_SAMPLE = 2;
const CHUNK_BYTES = CHUNK_SAMPLES * BYTES_PER_SAMPLE;
const FULL_SCALE = 32768;
const MIN_SAMPLE = -32768;
const MAX_SAMPLE = 32767;

function quantize(sample: number): number {
  return Math.max(MIN_SAMPLE, Math.min(MAX_SAMPLE, Math.round(sample * FULL_SCALE)));
}

// The graph hands over 128 samples at a time. Posting each quantum on would put
// hundreds of messages and socket frames per second on the wire, so samples
// gather here until a chunk is full.
class Pcm16Chunks {
  private buffer = new ArrayBuffer(CHUNK_BYTES);
  private samples = new Int16Array(this.buffer);
  private filled = 0;

  *fill(input: Float32Array): Generator<ArrayBuffer> {
    for (const sample of input) {
      this.samples[this.filled++] = quantize(sample);
      if (this.filled === CHUNK_SAMPLES) yield this.take();
    }
  }

  private take(): ArrayBuffer {
    const full = this.buffer;
    this.buffer = new ArrayBuffer(CHUNK_BYTES);
    this.samples = new Int16Array(this.buffer);
    this.filled = 0;
    return full;
  }
}

class PcmEncoder extends AudioWorkletProcessor {
  private readonly chunks = new Pcm16Chunks();

  process(inputs: Float32Array[][]): boolean {
    const channel = inputs[0]?.[0];
    if (channel) {
      for (const chunk of this.chunks.fill(channel)) this.port.postMessage(chunk, [chunk]);
    }
    return true;
  }
}

registerProcessor(PCM_ENCODER, PcmEncoder);
