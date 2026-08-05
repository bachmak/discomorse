import { useStore } from "../store";
import type { PlaybackRate } from "./playbackClock";
import { TimedPlayback } from "./timedPlayback";

// A decoded file runs faster than it was keyed, because sitting through a
// recording in full is rarely what the reader came for. Slow mode is how they
// ask for the real thing.
const FAST = 4;
const REALTIME = 1;

class SlowModeRate implements PlaybackRate {
  multiplier(): number {
    return useStore.getState().slowMode ? REALTIME : FAST;
  }
}

// One playback belongs to one session: whatever it still holds dies with it, so
// an abandoned run can never commit its tail into the store of the next one.
export function storePlayback(): TimedPlayback {
  return new TimedPlayback(useStore.getState(), new SlowModeRate());
}
