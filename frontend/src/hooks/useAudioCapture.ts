import { useRef } from "react";
import type { MicHandshake } from "../types/ws";

const CHUNK_SAMPLES = 2048;

export function useAudioCapture(onData: (data: ArrayBuffer | string) => void) {
  const streamRef = useRef<MediaStream | null>(null);

  const start = async () => {
    streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const handshake: MicHandshake = {sample_rate: ctx.sampleRate};
    onData(JSON.stringify(handshake))
    const source = ctx.createMediaStreamSource(streamRef.current);

    source.connect(ctx.destination);

    const processor = ctx.createScriptProcessor(CHUNK_SAMPLES, 1, 1);
    processor.onaudioprocess = async (e) => {
      const float32 = e.inputBuffer.getChannelData(0);
      const int16 = new Int16Array(float32.length);
      for (let i = 0; i < float32.length; i++) {
        int16[i] = Math.max(-32768, Math.min(32767, float32[i] * 32768));
      }
      onData(int16.buffer);
    };
    source.connect(processor);
    processor.connect(ctx.destination);
  };

  const stop = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  };

  return { start, stop };
}
