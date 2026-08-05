export interface Clock {
  nowMs(): number;
}

export class PerformanceClock implements Clock {
  nowMs(): number {
    return performance.now();
  }
}

const NO_EASING = 0;

/** The half-life a reader who asked the system for less motion should sit through. */
export function preferredHalfLife(ms: number): number {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? NO_EASING : ms;
}

// Follows a value that grows in bursts — whatever the network handed over since
// the last frame. Jumping to it reads as a lurch, so what is shown closes half
// the remaining distance every half-life instead: after a few frames the two
// move at the same speed, one small lag apart.
export class Glide {
  private shown: number | null = null;
  private readAtMs: number | null = null;

  constructor(
    private readonly halfLifeMs: number,
    private readonly clock: Clock = new PerformanceClock(),
  ) {}

  towards(target: number): number {
    this.shown = this.eased(target, this.sinceLastRead());
    return this.shown;
  }

  // A target that moved backwards belongs to a new run, not to this one.
  private eased(target: number, elapsedMs: number): number {
    if (this.shown === null || target < this.shown) return target;
    return target - (target - this.shown) * this.remaining(elapsedMs);
  }

  private remaining(elapsedMs: number): number {
    if (this.halfLifeMs <= NO_EASING) return 0;
    return 0.5 ** (elapsedMs / this.halfLifeMs);
  }

  private sinceLastRead(): number {
    const now = this.clock.nowMs();
    const elapsed = this.readAtMs === null ? 0 : now - this.readAtMs;
    this.readAtMs = now;
    return elapsed;
  }
}
