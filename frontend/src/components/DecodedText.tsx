import { useStore } from "../store";
import { CopyButton } from "./CopyButton";

interface DecodedLineProps {
  className: string;
  value: string;
  label: string;
  placeholder: string;
}

function DecodedLine({ className, value, label, placeholder }: DecodedLineProps) {
  return (
    <div className="decoded-line">
      <pre className={className}>
        {value || <span className="placeholder">{placeholder}</span>}
      </pre>
      <CopyButton value={value} target={label} />
    </div>
  );
}

export function DecodedText() {
  const morse = useStore((s) => s.decodedMorse);
  const symbols = useStore((s) => s.decodedSymbols);
  const text = useStore((s) => s.correctedText);
  const clearDecoded = useStore((s) => s.clearDecoded);

  return (
    <div className="decoded-body">
      <DecodedLine
        className="text"
        value={text}
        label="corrected text"
        placeholder="Corrected text will appear here…"
      />
      <DecodedLine
        className="symbols"
        value={symbols}
        label="raw text"
        placeholder="Raw text will appear here…"
      />
      <DecodedLine
        className="morse"
        value={morse}
        label="morse elements"
        placeholder="Morse elements will appear here…"
      />
      <button onClick={clearDecoded}>Clear</button>
    </div>
  );
}
