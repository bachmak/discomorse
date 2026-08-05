import { PresentationLink } from "./PresentationLink";
import { SlowModeToggle } from "./SlowModeToggle";
import { ThemeToggle } from "./ThemeToggle";

interface AppHeaderProps {
  demo: boolean;
}

export function AppHeader({ demo }: AppHeaderProps) {
  return (
    <header className="app-header">
      <h1>Discomorse</h1>
      <span className="tagline">Morse and CW audio, decoded to text.</span>
      <div className="header-actions">
        {demo && (
          <>
            <SlowModeToggle />
            <span className="demo-badge">DEMO</span>
          </>
        )}
        <PresentationLink />
        <ThemeToggle />
      </div>
    </header>
  );
}
