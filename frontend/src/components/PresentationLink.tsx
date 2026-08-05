const LABEL = "Architecture slides";

export function PresentationLink() {
  return (
    <a className="presentation-link" href="/presentation/" title={LABEL} aria-label={LABEL}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M4 5h16v11H4zM12 5V3M9.9 8.6l4.4 2.4-4.4 2.4z" />
      </svg>
    </a>
  );
}
