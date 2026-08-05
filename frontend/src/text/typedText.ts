import { Glide, preferredHalfLife } from "../pacing/glide";

// Long enough to read as typing, short enough that the line never trails the
// decoder by more than a glance.
const HALF_LIFE_MS = 90;
const LAST_CHARACTER = 1;

// A line the decoder appends to in bursts — a whole word the moment the
// corrector settles on it — handed to the screen one character after another.
export class TypedText {
  private readonly glide = new Glide(preferredHalfLife(HALF_LIFE_MS));

  shownOf(full: string): string {
    return full.slice(0, this.shownLength(full.length));
  }

  // Easing approaches its target without arriving, so the last character of a
  // line that has stopped growing is given rather than waited for.
  private shownLength(total: number): number {
    const shown = this.glide.towards(total);
    return total - shown < LAST_CHARACTER ? total : Math.floor(shown);
  }
}
