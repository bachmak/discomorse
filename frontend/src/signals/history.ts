import { HOP_RATE_HZ } from "../audioFormat";

// History deep enough to scroll back through, not just the visible window.
export const SPECTRUM_HISTORY_FRAMES = 2000;
const KEYING_HISTORY_SECONDS = 30;
export const MAX_KEYING_SAMPLES = KEYING_HISTORY_SECONDS * HOP_RATE_HZ;

// A list that has grown by nothing keeps its identity, so a subscriber reading
// it can tell "no new samples" from "the tail moved" by reference alone.
export function appendCapped<T>(current: T[], incoming: readonly T[], cap: number): T[] {
  if (incoming.length === 0) return current;
  return [...current, ...incoming].slice(-cap);
}
