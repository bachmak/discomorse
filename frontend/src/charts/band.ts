import { clamp } from "./numbers";
import { Range } from "./ticks";
import { furthestOffset, type Bounds, type Draggable } from "./window";

// A window over a fixed axis, anchored from its low end: the slice of the
// spectrum a chart shows, measured in the axis' own unit rather than in pixels.
export class Band implements Draggable<Band> {
  constructor(
    readonly span: number,
    readonly start: number = 0,
  ) {}

  get range(): Range {
    return new Range(this.start, this.start + this.span);
  }

  dragged(units: number, bounds: Bounds): Band {
    return this.at(this.start - units, this.span, bounds);
  }

  zoomed(factor: number, anchor: number, bounds: Bounds): Band {
    const span = clamp(this.span * factor, bounds.limits.min, bounds.limits.max);
    return this.at(this.start + (this.span - span) * anchor, span, bounds);
  }

  private at(start: number, span: number, bounds: Bounds): Band {
    return new Band(span, clamp(start, 0, furthestOffset(span, bounds.total)));
  }
}
