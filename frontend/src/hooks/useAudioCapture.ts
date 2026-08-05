import { useRef } from "react";
import { SUBSCRIPTION } from "../api/subscription";
import { MicCapture } from "../audio/micCapture";
import type { MicHandshakeMessage } from "../types/ws";

type Send = (data: ArrayBuffer | string) => void;

function handshake(sampleRate: number): string {
  const message: MicHandshakeMessage = {
    sample_rate: sampleRate,
    subscription: SUBSCRIPTION,
  };
  return JSON.stringify(message);
}

export function useAudioCapture() {
  const captureRef = useRef<MicCapture | null>(null);

  const start = async (send: Send): Promise<void> => {
    if (captureRef.current) return;
    const capture = await MicCapture.open();
    captureRef.current = capture;
    send(handshake(capture.sampleRate));
    capture.stream(send);
  };

  const stop = (): void => {
    void captureRef.current?.close();
    captureRef.current = null;
  };

  return { start, stop };
}
