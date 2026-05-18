import { useStore } from "../store";

export function DecodedText() {
  const text = useStore((s) => s.decodedText);
  const clearText = useStore((s) => s.clearText);

  return (
    <div>
      <pre style={{ minHeight: "4em", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
        {text || <span style={{ opacity: 0.4 }}>Decoded text will appear here…</span>}
      </pre>
      <button onClick={clearText}>Clear</button>
    </div>
  );
}
