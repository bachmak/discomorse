import { useAudioCapture } from "./hooks/useAudioCapture";
import { useWebSocket } from "./hooks/useWebSocket";
import { useDemoSignal } from "./hooks/useDemoSignal";
import { FilePicker } from "./components/FilePicker";
import { DecodedText } from "./components/DecodedText";
import { FFTSpectrum } from "./components/FFTSpectrum";
import { Oscilloscope } from "./components/Oscilloscope";
import { Waterfall } from "./components/Waterfall";

function demoRequested(): boolean {
  return import.meta.env.DEV && new URLSearchParams(window.location.search).has("demo");
}

export function App() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const { send } = useWebSocket(`${wsProtocol}//${window.location.host}/ws/mic`);
  const { start, stop } = useAudioCapture(send);
  useDemoSignal(demoRequested());

  return (
    <main>
      <h1>Morse Decoder</h1>
      <FilePicker />
      <div>
        <button onClick={() => { void start(); }}>Start mic</button>
        <button onClick={stop}>Stop mic</button>
      </div>
      <Oscilloscope />
      <FFTSpectrum />
      <Waterfall />
      <DecodedText />
    </main>
  );
}
