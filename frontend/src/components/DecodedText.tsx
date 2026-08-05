import { useStore } from "../store";
import { useTypedDecoded } from "../hooks/useTypedDecoded";
import type { DecodedLines } from "../text/decodedLines";
import { StreamingLine } from "./StreamingLine";

interface LineSpec {
  name: keyof DecodedLines;
  label: string;
  placeholder: string;
}

const LINES: LineSpec[] = [
  { name: "text", label: "corrected text", placeholder: "Corrected text will appear here…" },
  { name: "symbols", label: "raw text", placeholder: "Raw text will appear here…" },
  { name: "morse", label: "morse elements", placeholder: "Morse elements will appear here…" },
];

export function DecodedText() {
  const full = useStore((s) => s.decoded);
  const shown = useTypedDecoded();
  const clearDecoded = useStore((s) => s.clearDecoded);

  return (
    <div className="decoded-body">
      {LINES.map(({ name, label, placeholder }) => (
        <StreamingLine
          key={name}
          className={name}
          shown={shown[name]}
          full={full[name]}
          label={label}
          placeholder={placeholder}
        />
      ))}
      <button onClick={clearDecoded}>Clear</button>
    </div>
  );
}
