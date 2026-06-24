import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocket } from "../hooks/useWebSocket";

function micWsUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/mic`;
}

export function MicControls() {
  const { send } = useWebSocket(micWsUrl());
  const { start, stop } = useAudioCapture(send);

  return (
    <div className="mic">
      <button onClick={() => { void start(); }}>Start mic</button>
      <button onClick={stop}>Stop mic</button>
    </div>
  );
}
