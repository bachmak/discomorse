import { useRef } from "react";
import type { MicHandshakeMessage } from "../types/ws";

const CHUNK_SAMPLES = 2048;
const FULL_SCALE = 32768;
const MIN_SAMPLE = -32768;
const MAX_SAMPLE = 32767;

type Send = (data: ArrayBuffer | string) => void;

function toPcm16(samples: Float32Array): ArrayBuffer {
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    pcm[i] = Math.max(MIN_SAMPLE, Math.min(MAX_SAMPLE, Math.round(samples[i] * FULL_SCALE)));
  }
  return pcm.buffer;
}

function handshake(sampleRate: number): string {
  const message: MicHandshakeMessage = { sample_rate: sampleRate };
  return JSON.stringify(message);
}

class MicCapture {
  private readonly context = new AudioContext();
  private readonly source: MediaStreamAudioSourceNode;
  private readonly processor: ScriptProcessorNode;

  constructor(
    private readonly stream: MediaStream,
    send: Send,
  ) {
    send(handshake(this.context.sampleRate));
    this.source = this.context.createMediaStreamSource(stream);
    this.processor = this.context.createScriptProcessor(CHUNK_SAMPLES, 1, 1);
    this.processor.onaudioprocess = (event) =>
      send(toPcm16(event.inputBuffer.getChannelData(0)));
    this.source.connect(this.processor);
    // The processor writes no output, so this keeps it running without
    // putting the microphone on the speakers.
    this.processor.connect(this.context.destination);
  }

  async close(): Promise<void> {
    this.processor.onaudioprocess = null;
    this.processor.disconnect();
    this.source.disconnect();
    this.stream.getTracks().forEach((track) => track.stop());
    await this.context.close();
  }
}

export function useAudioCapture() {
  const captureRef = useRef<MicCapture | null>(null);

  const start = async (send: Send): Promise<void> => {
    if (captureRef.current) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    captureRef.current = new MicCapture(stream, send);
  };

  const stop = (): void => {
    void captureRef.current?.close();
    captureRef.current = null;
  };

  return { start, stop };
}
