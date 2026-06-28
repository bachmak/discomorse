import { useDemoSignal } from "./hooks/useDemoSignal";
import { AppHeader } from "./components/AppHeader";
import { Panel } from "./components/Panel";
import { SourceControls } from "./components/SourceControls";
import { DecodedText } from "./components/DecodedText";
import { Oscilloscope } from "./components/Oscilloscope";
import { FFTSpectrum } from "./components/FFTSpectrum";
import { Waterfall } from "./components/Waterfall";

function demoRequested(): boolean {
  return new URLSearchParams(window.location.search).has("demo");
}

export function App() {
  const demo = demoRequested();
  useDemoSignal(demo);

  return (
    <div className="app">
      <AppHeader demo={demo} />

      <Panel
        className="source"
        title="Source"
        hint="Upload a recording or decode live from the mic. Audio is processed on the server."
      >
        <SourceControls />
      </Panel>

      <Panel
        className="decoded"
        title="Decoded text"
        hint="Characters the decoder recovers from the keying."
      >
        <DecodedText />
      </Panel>

      <div className="signal-grid">
        <Panel
          title="Oscilloscope"
          hint="Time-domain keying. Short dits, longer dahs, and the gaps between them."
        >
          <Oscilloscope />
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
