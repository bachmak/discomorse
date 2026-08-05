import { useEffect } from "react";
import { useStore } from "../store";
import { binFrequency } from "../audioFormat";
import { AXIS_HEIGHT, FrequencyAxis, axisCaption, type AxisGeometry } from "../charts/axis";
import { clamp01 } from "../charts/numbers";
import type { Range } from "../charts/ticks";
import { useChartPalette } from "../charts/palette";
import type { ChartSurface } from "../charts/surface";
import { useChartView } from "../hooks/useChartView";
import { useCanvasSize, prepareSurface } from "./canvas";
import { ChartCanvas } from "./ChartCanvas";
import { BAND_BOUNDS, BAND_VIEW } from "./frequencyBand";

const HEIGHT = 150;
const PLOT_HEIGHT = HEIGHT - AXIS_HEIGHT;

const FREQUENCY_AXIS = new FrequencyAxis();

function geometry(width: number): AxisGeometry {
  return { width, tickTop: 0, tickBottom: PLOT_HEIGHT, labelY: HEIGHT - 6, labelInset: 14 };
}

// Bins outside the band are drawn too, off canvas, so the trace enters and
// leaves the plot at the right slope instead of dropping to the floor.
function drawSpectrum(
  { ctx, palette }: ChartSurface,
  data: number[],
  band: Range,
  width: number,
): void {
  const x = (bin: number) => band.fractionOf(binFrequency(bin, data.length)) * width;
  ctx.beginPath();
  ctx.moveTo(x(0), PLOT_HEIGHT);
  data.forEach((mag, bin) => ctx.lineTo(x(bin), PLOT_HEIGHT - clamp01(mag) * PLOT_HEIGHT));
  ctx.lineTo(x(data.length - 1), PLOT_HEIGHT);
  ctx.closePath();
  ctx.fillStyle = palette.fill;
  ctx.fill();
  ctx.strokeStyle = palette.trace;
  ctx.lineWidth = 1;
  ctx.stroke();
}

function drawHint({ ctx, palette }: ChartSurface, width: number): void {
  ctx.fillStyle = palette.hint;
  ctx.font = "13px ui-monospace, monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for signal…", width / 2, PLOT_HEIGHT / 2);
}

function drawFrame(surface: ChartSurface, data: number[], band: Range, width: number): void {
  FREQUENCY_AXIS.draw(surface, band, geometry(width));
  if (data.length > 0) drawSpectrum(surface, data, band, width);
  else drawHint(surface, width);
  axisCaption(surface, "Magnitude");
}

export function FFTSpectrum() {
  const { ref, size } = useCanvasSize(HEIGHT);
  const palette = useChartPalette();
  const frame = useStore((s) => s.spectrumFrames[s.spectrumFrames.length - 1]);
  const { view: band, goHome } = useChartView(ref, BAND_BOUNDS, BAND_VIEW);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || size.width === 0) return;
    const surface = prepareSurface(canvas, size, palette);
    if (surface) drawFrame(surface, frame?.data ?? [], band.range, size.width);
  }, [ref, frame, band, size.width, size.height, palette]);

  return <ChartCanvas canvasRef={ref} height={HEIGHT} onReset={goHome} />;
}
