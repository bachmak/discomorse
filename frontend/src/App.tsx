import { useAudioCapture } from "./hooks/useAudioCapture";
import { useWebSocket } from "./hooks/useWebSocket";
import { DecodedText } from "./components/DecodedText";
import { FFTSpectrum } from "./components/FFTSpectrum";
import { Waterfall } from "./components/Waterfall";

export function App() {
  const { send } = useWebSocket(`ws://${window.location.host}/ws/mic`);
  const { start, stop } = useAudioCapture(send);

  return (
    <main>
      <h1>Morse Decoder</h1>
      <div>
        <button onClick={() => { void start(); }}>Start</button>
        <button onClick={stop}>Stop</button>
      </div>
      <FFTSpectrum />
      <Waterfall />
      <DecodedText />
    </main>
  );
}
