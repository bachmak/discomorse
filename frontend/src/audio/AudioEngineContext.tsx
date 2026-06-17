import {
  createContext,
  useContext,
  useRef,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { AudioEngine } from "./AudioEngine";
import type { TransportState } from "./TransportState";

const EngineContext = createContext<AudioEngine | null>(null);

export function AudioEngineProvider({ children }: { children: ReactNode }) {
  const ref = useRef<AudioEngine | null>(null);
  if (ref.current === null) ref.current = new AudioEngine();
  return <EngineContext.Provider value={ref.current}>{children}</EngineContext.Provider>;
}

export function useAudioEngine(): AudioEngine {
  const engine = useContext(EngineContext);
  if (!engine) throw new Error("useAudioEngine must be used within an AudioEngineProvider");
  return engine;
}

export function useTransport(): TransportState {
  const engine = useAudioEngine();
  return useSyncExternalStore(engine.subscribe, engine.getState);
}
