import { clamp } from "./numbers";
import { furthestOffset, type Bounds, type Draggable, type ItemWindow } from "./window";

// A window over the tail of a growing buffer, measured in items rather than
// pixels. `back` is the distance from the newest item, so a viewport that has
// never been dragged stays glued to live data as the buffer grows.
export class Viewport implements Draggable<Viewport> {
  constructor(
    readonly span: number,
    readonly back: number = 0,
  ) {}

  get live(): boolean {
    return this.back === 0;
  }

  dragged(items: number, bounds: Bounds): Viewport {
    const back = clamp(this.back + items, 0, furthestOffset(this.span, bounds.total));
    return new Viewport(this.span, back);
  }

  zoomed(factor: number, anchor: number, bounds: Bounds): Viewport {
    const span = clamp(this.span * factor, bounds.limits.min, bounds.limits.max);
    const back = this.back + (this.span - span) * (1 - anchor);
    return new Viewport(span, clamp(back, 0, furthestOffset(span, bounds.total)));
  }

  atLive(): Viewport {
    return new Viewport(this.span);
  }

  window(total: number): ItemWindow {
    const to = total - Math.min(this.back, furthestOffset(this.span, total));
    return { from: to - this.span, to };
  }
}
