import { useEffect, useRef } from "react";
import { useStore } from "../store";
import type { ServerMessage } from "../types/ws";

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const { pushWaterfall, pushFFT, appendScope, setScope, appendText } = useStore();

  useEffect(() => {
    ws.current = new WebSocket(url);
    ws.current.binaryType = "arraybuffer";

    ws.current.onmessage = (ev) => {
      const msg: ServerMessage = JSON.parse(ev.data as string);
      if (msg.type === "waterfall") pushWaterfall(msg);
      else if (msg.type === "fft") pushFFT(msg);
      else if (msg.type === "oscilloscope")
        (msg.mode === "append" ? appendScope : setScope)(msg.data);
      else if (msg.type === "text") appendText(msg.data);
    };

    return () => ws.current?.close();
  }, [url]);

  const send = (chunk: ArrayBuffer) => ws.current?.send(chunk);

  return { send };
}
