import type { ThemeChoice } from "../theme/themeChoice";
import { useTheme } from "../theme/useTheme";

interface ThemeIcon {
  label: string;
  path: string;
}

const ICONS: Record<ThemeChoice, ThemeIcon> = {
  system: { label: "Theme: system", path: "M3 5h18v11H3zM9 20h6M12 16v4" },
  light: {
    label: "Theme: light",
    path:
      "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v2M12 20v2M4.9 4.9l1.4 1.4" +
      "M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
  },
  dark: { label: "Theme: dark", path: "M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z" },
};

export function ThemeToggle() {
  const { choice, cycle } = useTheme();
  const icon = ICONS[choice];

  return (
    <button
      className="theme-toggle"
      onClick={cycle}
      title={`${icon.label} — click to switch`}
      aria-label={icon.label}
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
