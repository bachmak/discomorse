import type { Gesture } from "./gestures";

// What one axis of a chart is made of: where its view starts, what pointer
// gestures do to it, and where a double-click sends it back to.
export interface ChartViewSetup<V> {
  gesture: Gesture<V>;
  initial: V;
  home(view: V): V;
}
