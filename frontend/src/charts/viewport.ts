export interface SpanLimits {
  min: number;
  max: number;
}

export interface Bounds {
  total: number;
  limits: SpanLimits;
}

export interface ItemWindow {
  from: number;
  to: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function furthestBack(span: number, total: number): number {
  return Math.max(0, total - span);
}

// A window over the tail of a growing buffer, measured in items rather than
// pixels. `back` is the distance from the newest item, so a viewport that has
// never been dragged stays glued to live data as the buffer grows.
export class Viewport {
  constructor(
    readonly span: number,
    readonly back: number = 0,
  ) {}

  get live(): boolean {
    return this.back === 0;
  }

  panned(items: number, bounds: Bounds): Viewport {
    return new Viewport(this.span, clamp(this.back + items, 0, furthestBack(this.span, bounds.total)));
  }

  zoomed(factor: number, anchor: number, bounds: Bounds): Viewport {
    const span = clamp(this.span * factor, bounds.limits.min, bounds.limits.max);
    const back = this.back + (this.span - span) * (1 - anchor);
    return new Viewport(span, clamp(back, 0, furthestBack(span, bounds.total)));
  }

  atLive(): Viewport {
    return new Viewport(this.span);
  }

  window(total: number): ItemWindow {
    const to = total - Math.min(this.back, furthestBack(this.span, total));
    return { from: to - this.span, to };
  }
}
