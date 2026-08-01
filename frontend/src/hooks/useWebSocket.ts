import { useEffect, useRef, useState } from "react";
import { MessageRouter } from "../messages/messageRouter";
import { storeSink } from "../messages/storeSink";

export function useWebSocket(url: string) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(url);
    const router = new MessageRouter(storeSink());
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => router.route(event.data as string);
    socketRef.current = socket;

    return () => socket.close();
  }, [url]);

  const send = (data: ArrayBuffer | string): void => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) socket.send(data);
  };

  return { send, connected };
}
