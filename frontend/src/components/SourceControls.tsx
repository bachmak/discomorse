import { FilePicker } from "./FilePicker";

interface SourceControlsProps {
  onStart: () => Promise<void>;
  onStop: () => void;
}

export function SourceControls({ onStart, onStop }: SourceControlsProps) {
  return (
    <div className="controls">
      <FilePicker />
      <span className="divider" aria-hidden="true" />
      <div className="mic">
        <button onClick={() => { void onStart(); }}>Start mic</button>
        <button onClick={onStop}>Stop mic</button>
      </div>
    </div>
  );
}
