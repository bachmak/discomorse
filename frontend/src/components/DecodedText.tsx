import { useStore } from "../store";

interface DecodedLineProps {
  className: string;
  value: string;
  placeholder: string;
}

function DecodedLine({ className, value, placeholder }: DecodedLineProps) {
  return (
    <pre className={className}>
      {value || <span className="placeholder">{placeholder}</span>}
    </pre>
  );
}

export function DecodedText() {
  const morse = useStore((s) => s.decodedMorse);
  const text = useStore((s) => s.correctedText);
  const clearDecoded = useStore((s) => s.clearDecoded);

  return (
    <div>
      <DecodedLine className="text" value={text} placeholder="Decoded text will appear here…" />
      <DecodedLine className="morse" value={morse} placeholder="Morse elements will appear here…" />
      <button onClick={clearDecoded}>Clear</button>
    </div>
  );
}
