import { useRef, type ChangeEvent } from "react";
import { useFileDecoder } from "../hooks/useFileDecoder";

export function FilePicker() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { status, decode } = useFileDecoder();

  const onSelect = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (file) void decode(file);
  };

  return (
    <div>
      <button onClick={() => inputRef.current?.click()}>Browse audio…</button>
      <input ref={inputRef} type="file" accept="audio/*" hidden onChange={onSelect} />
      {status && <span role="status">{status}</span>}
    </div>
  );
}
