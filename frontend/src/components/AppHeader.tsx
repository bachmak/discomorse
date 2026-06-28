import { SlowModeToggle } from "./SlowModeToggle";

interface AppHeaderProps {
  demo: boolean;
}

export function AppHeader({ demo }: AppHeaderProps) {
  return (
    <header className="app-header">
      <h1>Discomorse</h1>
      <span className="tagline">Morse and CW audio, decoded to text.</span>
      {demo && (
        <div className="header-actions">
          <SlowModeToggle />
          <span className="demo-badge">DEMO</span>
        </div>
      )}
    </header>
  );
}
