import { micSocketUrl } from "../api/endpoints";
import { useMicSession, type MicStatus } from "../hooks/useMicSession";

const STATUS_LABELS: Record<MicStatus, string> = {
  idle: "",
  connecting: "Connecting…",
  listening: "Listening…",
  offline: "Decoder offline",
  blocked: "Microphone unavailable",
};

const BUSY: readonly MicStatus[] = ["connecting", "listening"];

export function MicControls() {
  const { status, start, stop } = useMicSession(micSocketUrl());
  const label = STATUS_LABELS[status];

  return (
    <div className="mic">
      <button disabled={BUSY.includes(status)} onClick={() => { void start(); }}>Start mic</button>
      <button disabled={status !== "listening"} onClick={stop}>Stop mic</button>
      {label && <span role="status">{label}</span>}
    </div>
  );
}
