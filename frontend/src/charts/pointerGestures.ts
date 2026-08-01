import type { Gesture, PlotBox } from "./gestures";
import type { Bounds, Viewport } from "./viewport";

export type ApplyGesture = (change: (view: Viewport, bounds: Bounds) => Viewport) => void;

interface DragOrigin {
  x: number;
  y: number;
}

/** Translates wheel and pointer events on an element into viewport changes. */
export class PointerGestures {
  private origin: DragOrigin | null = null;

  constructor(
    private readonly target: HTMLElement,
    private readonly gesture: Gesture,
    private readonly apply: ApplyGesture,
  ) {}

  attach(): void {
    this.target.addEventListener("wheel", this.onWheel, { passive: false });
    this.target.addEventListener("pointerdown", this.onPointerDown);
    window.addEventListener("pointermove", this.onPointerMove);
    window.addEventListener("pointerup", this.onPointerEnd);
    window.addEventListener("pointercancel", this.onPointerEnd);
  }

  detach(): void {
    this.target.removeEventListener("wheel", this.onWheel);
    this.target.removeEventListener("pointerdown", this.onPointerDown);
    window.removeEventListener("pointermove", this.onPointerMove);
    window.removeEventListener("pointerup", this.onPointerEnd);
    window.removeEventListener("pointercancel", this.onPointerEnd);
  }

  private readonly onWheel = (event: WheelEvent): void => {
    event.preventDefault();
    this.apply((view, bounds) => this.gesture.wheel(view, event, this.context(bounds)));
  };

  private readonly onPointerDown = (event: PointerEvent): void => {
    this.origin = { x: event.clientX, y: event.clientY };
  };

  private readonly onPointerMove = (event: PointerEvent): void => {
    if (!this.origin) return;
    const delta = { dx: event.clientX - this.origin.x, dy: event.clientY - this.origin.y };
    this.origin = { x: event.clientX, y: event.clientY };
    this.apply((view, bounds) => this.gesture.drag(view, delta, this.context(bounds)));
  };

  private readonly onPointerEnd = (): void => {
    this.origin = null;
  };

  private context(bounds: Bounds): { plot: PlotBox; bounds: Bounds } {
    const rect = this.target.getBoundingClientRect();
    return { plot: { width: rect.width, height: rect.height }, bounds };
  }
}
