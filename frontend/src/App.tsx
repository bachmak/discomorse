import { useAudioCapture } from "./hooks/useAudioCapture";
import { useWebSocket } from "./hooks/useWebSocket";
import { AppHeader } from "./components/AppHeader";
import { Panel } from "./components/Panel";
import { SourceControls } from "./components/SourceControls";
import { SignalMetrics } from "./components/SignalMetrics";
import { Placeholder } from "./components/Placeholder";
import { DecodedText } from "./components/DecodedText";
import { FFTSpectrum } from "./components/FFTSpectrum";
import { Waterfall } from "./components/Waterfall";

function demoRequested(): boolean {
  return import.meta.env.DEV && new URLSearchParams(window.location.search).has("demo");
}

function micWsUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/mic`;
}

export function App() {
  const demo = demoRequested();
  const { send } = useWebSocket(micWsUrl());
  const { start, stop } = useAudioCapture(send);

  return (
    <div className="app">
      <AppHeader demo={demo} />

      <Panel
        className="source"
        title="Source"
        hint="Upload a recording or decode live from the mic. Audio is processed on the server."
      >
        <SourceControls onStart={start} onStop={stop} />
      </Panel>

      <Panel
        className="decoded"
        title="Decoded text"
        hint="Characters the decoder recovers from the keying."
      >
        <DecodedText />
      </Panel>

      <Panel title="Signal" hint="Live readouts once the decoder locks onto a signal.">
        <SignalMetrics />
      </Panel>

      <div className="signal-grid">
        <Panel
          title="Oscilloscope"
          hint="Time-domain keying. Short dits, longer dahs, and the gaps between them."
        >
          <Placeholder note="Waveform trace appears here once a signal arrives." />
        </Panel>

        <Panel title="Spectrum" hint="Instantaneous frequency content. The pitch of the CW tone.">
          <FFTSpectrum />
        </Panel>

        <Panel
          className="span-full"
          title="Waterfall"
          hint="Frequency over time. Locate the carrier and watch it drift or fade."
        >
          <Waterfall />
        </Panel>
      </div>
    </div>
  );
}
