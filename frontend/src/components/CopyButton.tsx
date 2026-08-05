import { useClipboard, type CopyState } from "../hooks/useClipboard";

interface CopyIcon {
  verb: string;
  path: string;
}

const ICONS: Record<CopyState, CopyIcon> = {
  idle: {
    verb: "Copy",
    path:
      "M11 9h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z" +
      "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1",
  },
  copied: { verb: "Copied", path: "M20 6L9 17l-5-5" },
  failed: { verb: "Copy failed for", path: "M18 6L6 18M6 6l12 12" },
};

interface CopyButtonProps {
  value: string;
  target: string;
}

export function CopyButton({ value, target }: CopyButtonProps) {
  const { state, copy } = useClipboard(value);
  const icon = ICONS[state];
  const label = `${icon.verb} ${target}`;

  return (
    <button
      className={`copy-button ${state}`}
      onClick={copy}
      disabled={!value}
      title={label}
      aria-label={label}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d={icon.path} />
      </svg>
    </button>
  );
}
