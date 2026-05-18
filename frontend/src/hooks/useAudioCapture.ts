import { useRef } from "react";

const TARGET_SAMPLE_RATE = 8000;
const CHUNK_SAMPLES = 2048;

export function useAudioCapture(onChunk: (pcm: ArrayBuffer) => void) {
  const streamRef = useRef<MediaStream | null>(null);

  const start = async () => {
    streamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(streamRef.current);

    const offline = new OfflineAudioContext(1, CHUNK_SAMPLES, TARGET_SAMPLE_RATE);
    const bufSrc = offline.createBufferSource();

    source.connect(ctx.destination);

    const processor = ctx.createScriptProcessor(CHUNK_SAMPLES, 1, 1);
    processor.onaudioprocess = async (e) => {
      const float32 = e.inputBuffer.getChannelData(0);
      const int16 = new Int16Array(float32.length);
      for (let i = 0; i < float32.length; i++) {
        int16[i] = Math.max(-32768, Math.min(32767, float32[i] * 32768));
      }
      onChunk(int16.buffer);
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
