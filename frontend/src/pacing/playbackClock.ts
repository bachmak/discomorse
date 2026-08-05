const MS_PER_SECOND = 1000;

export interface PlaybackRate {
  multiplier(): number;
}

// A playhead on the audio's own time axis, driven by the wall clock instead of
// by whatever the network happens to hand over — but never allowed past the
// last message that has arrived. A burst therefore fills the buffer rather than
// the screen, and a link that falls behind holds the playhead still rather than
// letting the backlog land in a single frame.
export class PlaybackClock {
  private position = 0;
  private readAtMs: number | null = null;

  constructor(private readonly rate: PlaybackRate) {}

  advanceTo(horizon: number): number {
    this.position = Math.min(this.position + this.elapsedAudioSeconds(), horizon);
    return this.position;
  }

  private elapsedAudioSeconds(): number {
    const now = performance.now();
    const sinceMs = this.readAtMs === null ? 0 : now - this.readAtMs;
    this.readAtMs = now;
    return (sinceMs / MS_PER_SECOND) * this.rate.multiplier();
  }
}
