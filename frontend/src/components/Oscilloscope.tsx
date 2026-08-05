import { useState } from "react";
import { useStore } from "../store";
import { HOP_RATE_HZ } from "../audioFormat";
import { MAX_KEYING_SAMPLES } from "../signals/history";
import type { ChartViewSetup } from "../charts/chartView";
import { ZoomAndPan } from "../charts/gestures";
import { SCOPE_HEIGHT, drawScope, type ScopePlot } from "../charts/keyTrace";
import { useChartPalette } from "../charts/palette";
import { Range } from "../charts/ticks";
import { Viewport } from "../charts/viewport";
import { shiftedBy, type Bounds, type ItemWindow } from "../charts/window";
import { Glide, preferredHalfLife } from "../pacing/glide";
import { useChartView } from "../hooks/useChartView";
import { useFrameLoop } from "../hooks/useFrameLoop";
import { useCanvasSize, prepareSurface } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";

// About a tenth of a second of catching up: enough to absorb a burst of
// arrivals, too little to notice the trace running behind the sound.
const HALF_LIFE_MS = 70;

const SCOPE_VIEW: ChartViewSetup<Viewport> = {
  gesture: new ZoomAndPan<Viewport>(),
  initial: new Viewport(4 * HOP_RATE_HZ),
  home: (view) => view.atLive(),
};

function scopeBounds(produced: number): Bounds {
  return { total: produced, limits: { min: 0.1 * HOP_RATE_HZ, max: MAX_KEYING_SAMPLES } };
}

function secondsAgo(window: ItemWindow, live: number): Range {
  return new Range((window.from - live) / HOP_RATE_HZ, (window.to - live) / HOP_RATE_HZ);
}

// The window is measured against the whole stream; only its tail is still held,
// so the plot reads that tail from wherever it starts.
function plotNow(view: Viewport, glide: Glide, width: number): ScopePlot {
  const keying = useStore.getState().keying;
  const live = glide.towards(keying.produced);
  const window = view.window(live);
  return {
    levels: keying.levels,
    window: shiftedBy(window, -keying.oldest),
    elapsed: secondsAgo(window, live),
    width,
  };
}

export function Oscilloscope() {
  const { ref, size } = useCanvasSize(SCOPE_HEIGHT);
  const palette = useChartPalette();
  const produced = useStore((s) => s.keying.produced);
  const { view, goHome } = useChartView(ref, scopeBounds(produced), SCOPE_VIEW);
  const [glide] = useState(() => new Glide(preferredHalfLife(HALF_LIFE_MS)));

  useFrameLoop(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    if (surface) drawScope(surface, plotNow(view, glide, size.width));
  });

  return <ChartCanvas canvasRef={ref} height={SCOPE_HEIGHT} onReset={goHome} />;
}
