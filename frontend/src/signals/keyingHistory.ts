import { MAX_KEYING_SAMPLES, appendCapped } from "./history";

const KEY_DOWN = 1;
const KEY_UP = 0;

function levelsOf(keying: readonly boolean[]): number[] {
  return keying.map((on) => (on ? KEY_DOWN : KEY_UP));
}

// The tail of the key trace, and how far along the stream that tail ends. A
// chart places its window against `produced`, which keeps counting once the
// tail is full and the oldest samples start falling off the front of it.
export class KeyingHistory {
  private constructor(
    readonly levels: number[],
    readonly produced: number,
  ) {}

  static empty(): KeyingHistory {
    return new KeyingHistory([], 0);
  }

  /** Where in the stream the first sample still held sits. */
  get oldest(): number {
    return this.produced - this.levels.length;
  }

  grownBy(keying: readonly boolean[]): KeyingHistory {
    if (keying.length === 0) return this;
    const grown = appendCapped(this.levels, levelsOf(keying), MAX_KEYING_SAMPLES);
    return new KeyingHistory(grown, this.produced + keying.length);
  }
}
