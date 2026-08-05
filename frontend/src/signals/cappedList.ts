// Holds the newest `cap` items of an unbounded run. Trimming in bulk once the
// overshoot is as long as the cap keeps appending cheap, which matters when a
// decoder feeds this hundreds of times per second.
export class CappedList<T> {
  private items: T[] = [];

  constructor(private readonly cap: number) {}

  get size(): number {
    return Math.min(this.items.length, this.cap);
  }

  add(item: T): void {
    this.items.push(item);
    if (this.items.length > this.cap * 2) this.trim();
  }

  take(): T[] {
    this.trim();
    const taken = this.items;
    this.items = [];
    return taken;
  }

  private trim(): void {
    if (this.items.length > this.cap) this.items = this.items.slice(-this.cap);
  }
}
