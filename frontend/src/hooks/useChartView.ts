import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import type { ChartViewSetup } from "../charts/chartView";
import { PointerGestures } from "../charts/pointerGestures";
import type { Bounds } from "../charts/window";

export interface ChartViewControl<V> {
  view: V;
  goHome: () => void;
}

/** Drives one axis of a chart: gestures on `target` move the view it returns. */
export function useChartView<V>(
  target: RefObject<HTMLElement>,
  bounds: Bounds,
  setup: ChartViewSetup<V>,
): ChartViewControl<V> {
  const [view, setView] = useState(setup.initial);
  const boundsRef = useRef(bounds);
  boundsRef.current = bounds;

  useEffect(() => {
    const element = target.current;
    if (!element) return;
    const gestures = new PointerGestures(element, setup.gesture, (change) =>
      setView((current) => change(current, boundsRef.current)),
    );
    gestures.attach();
    return () => gestures.detach();
  }, [target, setup]);

  return { view, goHome: () => setView(setup.home) };
}
