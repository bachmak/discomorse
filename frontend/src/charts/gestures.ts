import type { Bounds, Viewport } from "./viewport";

const ZOOM_RATE = 0.0015;
const LINE_PIXELS = 16;

export interface PlotBox {
  width: number;
  height: number;
}

export interface DragDelta {
  dx: number;
  dy: number;
}

export interface GestureContext {
  plot: PlotBox;
  bounds: Bounds;
}

export interface Gesture {
  wheel(view: Viewport, event: WheelEvent, context: GestureContext): Viewport;
  drag(view: Viewport, delta: DragDelta, context: GestureContext): Viewport;
}

function wheelPixels(event: WheelEvent, page: number): number {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * LINE_PIXELS;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * page;
  return event.deltaY;
}

function anchorAt(event: WheelEvent, width: number): number {
  return Math.min(1, Math.max(0, event.offsetX / width));
}

/** Wheel zooms the time axis around the cursor, dragging pans through history. */
export class ZoomAndPan implements Gesture {
  wheel(view: Viewport, event: WheelEvent, context: GestureContext): Viewport {
    const factor = Math.exp(wheelPixels(event, context.plot.width) * ZOOM_RATE);
    return view.zoomed(factor, anchorAt(event, context.plot.width), context.bounds);
  }

  drag(view: Viewport, delta: DragDelta, context: GestureContext): Viewport {
    return view.panned((delta.dx * view.span) / context.plot.width, context.bounds);
  }
}

/** Wheel and drag both scroll the view up into older rows. */
export class VerticalScroll implements Gesture {
  wheel(view: Viewport, event: WheelEvent, context: GestureContext): Viewport {
    const rows = (-wheelPixels(event, context.plot.height) * view.span) / context.plot.height;
    return view.panned(rows, context.bounds);
  }

  drag(view: Viewport, delta: DragDelta, context: GestureContext): Viewport {
    return view.panned((delta.dy * view.span) / context.plot.height, context.bounds);
  }
}
