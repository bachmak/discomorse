import { NYQUIST_HZ } from "../audioFormat";
import { Band } from "../charts/band";
import type { ChartViewSetup } from "../charts/chartView";
import { ZoomAndPan } from "../charts/gestures";
import type { Bounds } from "../charts/window";

// Morse tones live low in the band, so the spectrum charts open on the bottom
// 2 kHz instead of squeezing mostly empty spectrum into the same pixels.
const DEFAULT_SPAN_HZ = 2000;

// A couple of FFT bins wide at the backend's resolution; zooming past that only
// magnifies interpolation.
const MIN_SPAN_HZ = 200;

const DEFAULT_BAND = new Band(DEFAULT_SPAN_HZ);

export const BAND_BOUNDS: Bounds = {
  total: NYQUIST_HZ,
  limits: { min: MIN_SPAN_HZ, max: NYQUIST_HZ },
};

export const BAND_VIEW: ChartViewSetup<Band> = {
  gesture: new ZoomAndPan<Band>(),
  initial: DEFAULT_BAND,
  home: () => DEFAULT_BAND,
};
