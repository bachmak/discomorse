// Quarters rather than fifths, so a kilohertz axis ticks on 250 / 500 / 750
// instead of 200 / 400 / 600.
const NICE_FACTORS = [1, 2.5, 5, 10];
const EDGE_TOLERANCE = 1e-9;

export class Range {
  constructor(
    readonly min: number,
    readonly max: number,
  ) {}

  get span(): number {
    return this.max - this.min;
  }

  fractionOf(value: number): number {
    return (value - this.min) / this.span;
  }

  // The roundest step (1, 2, 2.5 or 5 times a power of ten) that keeps the
  // tick count at or below the budget the caller has room for.
  step(maxTicks: number): number {
    const rough = this.span / Math.max(1, maxTicks);
    const magnitude = 10 ** Math.floor(Math.log10(rough));
    const factor = NICE_FACTORS.find((candidate) => candidate * magnitude >= rough) ?? 10;
    return factor * magnitude;
  }

  ticks(step: number): number[] {
    const first = Math.ceil(this.min / step - EDGE_TOLERANCE);
    const last = Math.floor(this.max / step + EDGE_TOLERANCE);
    const count = Math.max(0, last - first + 1);
    return Array.from({ length: count }, (_unused, i) => (first + i) * step);
  }
}
