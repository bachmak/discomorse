import { useStickyScroll } from "../hooks/useStickyScroll";
import { CopyButton } from "./CopyButton";

// How much of the tail is still fading in. Further back the animation has long
// finished, and a character costs a span for nothing.
const FRESH_CHARACTERS = 24;

interface FreshProps {
  text: string;
  from: number;
}

// Keyed by its place in the line, so a character fades in once — when it is
// first typed — and not again as the ones behind it arrive.
function FreshCharacters({ text, from }: FreshProps) {
  return (
    <>
      {[...text].map((character, i) => (
        <span key={from + i} className="fresh">
          {character}
        </span>
      ))}
    </>
  );
}

interface LineBodyProps {
  shown: string;
  placeholder: string;
}

function LineBody({ shown, placeholder }: LineBodyProps) {
  if (!shown) return <span className="placeholder">{placeholder}</span>;
  const settled = shown.slice(0, Math.max(0, shown.length - FRESH_CHARACTERS));
  return (
    <>
      {settled}
      <FreshCharacters text={shown.slice(settled.length)} from={settled.length} />
      <span className="caret" aria-hidden="true" />
    </>
  );
}

interface StreamingLineProps {
  className: string;
  shown: string;
  full: string;
  label: string;
  placeholder: string;
}

/** One decoded line: typed out as far as it has come, copied in full. */
export function StreamingLine({ className, shown, full, label, placeholder }: StreamingLineProps) {
  const box = useStickyScroll<HTMLPreElement>(shown);

  return (
    <div className="decoded-line">
      <pre className={className} ref={box}>
        <LineBody shown={shown} placeholder={placeholder} />
      </pre>
      <CopyButton value={full} target={label} />
    </div>
  );
}
