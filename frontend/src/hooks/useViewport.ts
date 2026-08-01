import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import type { Gesture } from "../charts/gestures";
import { PointerGestures } from "../charts/pointerGestures";
import { Viewport, type SpanLimits } from "../charts/viewport";

export interface ViewportSetup {
  gesture: Gesture;
  span: number;
  limits: SpanLimits;
}

export interface ViewportControl {
  view: Viewport;
  goLive: () => void;
}

export function useViewport(
  target: RefObject<HTMLElement>,
  total: number,
  setup: ViewportSetup,
): ViewportControl {
  const [view, setView] = useState(() => new Viewport(setup.span));
  const totalRef = useRef(total);
  totalRef.current = total;

  useEffect(() => {
    const element = target.current;
    if (!element) return;
    const gestures = new PointerGestures(element, setup.gesture, (change) =>
      setView((current) => change(current, { total: totalRef.current, limits: setup.limits })),
    );
    gestures.attach();
    return () => gestures.detach();
  }, [target, setup]);

  return { view, goLive: () => setView((current) => current.atLive()) };
}
