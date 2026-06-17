import { useAudioEngine, useTransport } from "../audio/AudioEngineContext";
import { formatTime } from "../audio/format";

export function TransportControls() {
  const engine = useAudioEngine();
  const { playing, currentTime, duration, fileName } = useTransport();
  const disabled = fileName === null;

  return (
    <div>
      <button disabled={disabled} onClick={() => void engine.toggle()}>
        {playing ? "Pause" : "Play"}
      </button>
      <input
        type="range"
        min={0}
        max={duration}
        step={0.01}
        value={currentTime}
        disabled={disabled}
        onChange={(event) => engine.seek(Number(event.target.value))}
      />
      <span>
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
      {fileName && <span> · {fileName}</span>}
    </div>
  );
}
