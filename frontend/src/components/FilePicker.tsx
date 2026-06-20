import { useRef, useState, type ChangeEvent } from "react";

const UPLOAD_URL = "/upload";

export function FilePicker() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string | null>(null);

  const onSelect = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (!file) return;
    setStatus(`Sending ${file.name}…`);
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(UPLOAD_URL, { method: "POST", body });
      setStatus(response.ok ? `Sent ${file.name}` : `Upload failed (${response.status})`);
    } catch {
      setStatus(`Upload failed for ${file.name}`);
    }
  };

  return (
    <div>
      <button onClick={() => inputRef.current?.click()}>Browse audio…</button>
      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        hidden
        onChange={(event) => void onSelect(event)}
      />
      {status && <span role="status">{status}</span>}
    </div>
  );
}
