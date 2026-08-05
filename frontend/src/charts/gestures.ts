import type { Bounds, Draggable, PlotBox } from "./window";

const ZOOM_RATE = 0.0015;
const LINE_PIXELS = 16;

export interface DragDelta {
  dx: number;
  dy: number;
}

export interface GestureContext {
  plot: PlotBox;
  bounds: Bounds;
}

export interface Gesture<V> {
  wheel(view: V, event: WheelEvent, context: GestureContext): V;
  drag(view: V, delta: DragDelta, context: GestureContext): V;
}

function wheelPixels(event: WheelEvent, page: number): number {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * LINE_PIXELS;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * page;
  return event.deltaY;
}

function anchorAt(event: WheelEvent, width: number): number {
  return Math.min(1, Math.max(0, event.offsetX / width));
}

/** Wheel zooms the horizontal axis around the cursor, dragging pans along it. */
export class ZoomAndPan<V extends Draggable<V>> implements Gesture<V> {
  wheel(view: V, event: WheelEvent, context: GestureContext): V {
    const factor = Math.exp(wheelPixels(event, context.plot.width) * ZOOM_RATE);
    return view.zoomed(factor, anchorAt(event, context.plot.width), context.bounds);
  }

  drag(view: V, delta: DragDelta, context: GestureContext): V {
    return view.dragged((delta.dx * view.span) / context.plot.width, context.bounds);
  }
}

/** Drags the vertical axis; the wheel is left to the horizontal one. */
export class VerticalPan<V extends Draggable<V>> implements Gesture<V> {
  wheel(view: V): V {
    return view;
  }

  drag(view: V, delta: DragDelta, context: GestureContext): V {
    return view.dragged((delta.dy * view.span) / context.plot.height, context.bounds);
  }
}
