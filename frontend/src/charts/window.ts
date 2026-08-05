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

export interface PlotBox {
  width: number;
  height: number;
}

/** How far a window of `span` can move before it runs off the axis. */
export function furthestOffset(span: number, total: number): number {
  return Math.max(0, total - span);
}

/** The same window, counted from an origin `offset` items further back. */
export function shiftedBy(window: ItemWindow, offset: number): ItemWindow {
  return { from: window.from + offset, to: window.to + offset };
}

// A window a pointer can move over an axis. `dragged` follows the cursor, so
// positive units push the content the way the cursor went; `anchor` is the
// fraction of the window under the cursor, measured from its low edge.
export interface Draggable<V> {
  readonly span: number;
  dragged(units: number, bounds: Bounds): V;
  zoomed(factor: number, anchor: number, bounds: Bounds): V;
}
