import { useRef, useState, type ChangeEvent } from "react";
import { useAudioEngine } from "../audio/AudioEngineContext";

export function FilePicker() {
  const engine = useAudioEngine();
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const onSelect = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setError(null);
      await engine.load(file);
    } catch {
      setError(`Could not decode "${file.name}"`);
    }
  };

  return (
    <div>
      <button onClick={() => inputRef.current?.click()}>Browse MP3…</button>
      <input
        ref={inputRef}
        type="file"
        accept="audio/mpeg,audio/*"
        hidden
        onChange={(event) => void onSelect(event)}
      />
      {error && <span role="alert">{error}</span>}
    </div>
  );
}
