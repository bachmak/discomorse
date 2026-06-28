import { useStore } from "../store";

export function SlowModeToggle() {
  const slowMode = useStore((s) => s.slowMode);
  const setSlowMode = useStore((s) => s.setSlowMode);

  return (
    <label className="slow-toggle" title="Slow the charts down so the keying is readable">
      <input
        type="checkbox"
        role="switch"
        checked={slowMode}
        onChange={(event) => setSlowMode(event.target.checked)}
      />
      <span>Slow mode</span>
    </label>
  );
}
