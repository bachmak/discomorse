interface PlaceholderProps {
  note: string;
  minHeight?: number;
}

export function Placeholder({ note, minHeight = 160 }: PlaceholderProps) {
  return (
    <div className="placeholder" style={{ minHeight }}>
      <span className="placeholder-note">{note}</span>
    </div>
  );
}
