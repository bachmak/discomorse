import { FilePicker } from "./FilePicker";
import { MicControls } from "./MicControls";

export function SourceControls() {
  return (
    <div className="controls">
      <FilePicker />
      <span className="divider" aria-hidden="true" />
      <MicControls />
    </div>
  );
}
