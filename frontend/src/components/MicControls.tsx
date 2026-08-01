import { micSocketUrl } from "../api/endpoints";
import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocket } from "../hooks/useWebSocket";

export function MicControls() {
  const { send, connected } = useWebSocket(micSocketUrl());
  const { start, stop } = useAudioCapture(send);

  return (
    <div className="mic">
      <button disabled={!connected} onClick={() => { void start(); }}>Start mic</button>
      <button onClick={stop}>Stop mic</button>
      {!connected && <span role="status">Decoder offline</span>}
    </div>
  );
}
