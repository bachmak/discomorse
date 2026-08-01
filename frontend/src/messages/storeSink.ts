import { useStore } from "../store";
import type { MessageSink } from "./sink";

export function storeSink(): MessageSink {
  return useStore.getState();
}
