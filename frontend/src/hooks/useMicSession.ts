import { useRef, useState } from "react";
import { MicSocket, MicSocketError } from "../api/micSocket";
import { useStore } from "../store";
import { useAudioCapture } from "./useAudioCapture";

export type MicStatus = "idle" | "connecting" | "listening" | "offline" | "blocked";

export interface MicSession {
  status: MicStatus;
  start: () => Promise<void>;
  stop: () => void;
}

export function useMicSession(url: string): MicSession {
  const capture = useAudioCapture();
  const [status, setStatus] = useState<MicStatus>("idle");
  const socketRef = useRef<MicSocket | null>(null);

  const stop = (): void => {
    capture.stop();
    socketRef.current?.close();
    socketRef.current = null;
    setStatus("idle");
  };

  const dropped = (): void => {
    capture.stop();
    setStatus((current) => (current === "listening" ? "offline" : current));
  };

  const listen = async (): Promise<void> => {
    const socket = await MicSocket.open(url);
    socketRef.current = socket;
    void socket.closed().then(dropped);
    useStore.getState().reset();
    await capture.start(socket.send);
  };

  const start = async (): Promise<void> => {
    setStatus("connecting");
    try {
      await listen();
      setStatus("listening");
    } catch (error) {
      stop();
      setStatus(error instanceof MicSocketError ? "offline" : "blocked");
    }
  };

  return { status, start, stop };
}
