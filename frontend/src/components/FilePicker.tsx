import { useRef, type ChangeEvent } from "react";
import { useFileDecoder } from "../hooks/useFileDecoder";

export function FilePicker() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { status, source, decode, restart } = useFileDecoder();

  const onSelect = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) void decode(file);
  };

  return (
    <div>
      <button onClick={() => inputRef.current?.click()}>Browse audio…</button>
      <button disabled={!source} onClick={() => { void restart(); }}>
        Restart
      </button>
      <input ref={inputRef} type="file" accept="audio/*" hidden onChange={onSelect} />
      {status && <span role="status">{status}</span>}
    </div>
  );
}
