import { useAudioCapture } from "./hooks/useAudioCapture";
import { useWebSocket } from "./hooks/useWebSocket";
import { AudioEngineProvider } from "./audio/AudioEngineContext";
import { FilePicker } from "./components/FilePicker";
import { TransportControls } from "./components/TransportControls";
import { DecodedText } from "./components/DecodedText";
import { FFTSpectrum } from "./components/FFTSpectrum";
import { Waterfall } from "./components/Waterfall";

export function App() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const { send } = useWebSocket(`${wsProtocol}//${window.location.host}/ws/mic`);
  const { start, stop } = useAudioCapture(send);

  return (
    <AudioEngineProvider>
      <main>
        <h1>Morse Decoder</h1>
        <FilePicker />
        <TransportControls />
        <div>
          <button onClick={() => { void start(); }}>Start mic</button>
          <button onClick={stop}>Stop mic</button>
        </div>
        <FFTSpectrum />
        <Waterfall />
        <DecodedText />
      </main>
    </AudioEngineProvider>
  );
}
