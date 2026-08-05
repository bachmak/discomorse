import type { ChartSurface } from "./surface";
import type { Range } from "./ticks";

const AXIS_FONT = "12px ui-monospace, monospace";
const CAPTION_PAD = 5;
const CAPTION_TOP = 8;
const LABEL_GAP = 6;
const LABEL_PITCH = 52;
const MINOR_TICK_LENGTH = 6;
const MINORS_PER_MAJOR = 2;

export const AXIS_HEIGHT = 22;

export interface AxisGeometry {
  width: number;
  tickTop: number;
  tickBottom: number;
  labelY: number;
  labelInset: number;
}

export function axisLabel(
  { ctx, palette }: ChartSurface,
  text: string,
  x: number,
  y: number,
  align: CanvasTextAlign = "center",
): void {
  ctx.fillStyle = palette.label;
  ctx.font = AXIS_FONT;
  ctx.textAlign = align;
  ctx.textBaseline = "alphabetic";
  ctx.fillText(text, x, y);
}

export function axisCaption({ ctx, palette }: ChartSurface, text: string, left = 8): void {
  ctx.font = AXIS_FONT;
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  const width = ctx.measureText(text).width + CAPTION_PAD * 2;
  ctx.fillStyle = palette.captionBackground;
  ctx.beginPath();
  ctx.roundRect(left, CAPTION_TOP, width, 11 + CAPTION_PAD * 2, 4);
  ctx.fill();
  ctx.fillStyle = palette.label;
  ctx.fillText(text, left + CAPTION_PAD, CAPTION_TOP + CAPTION_PAD);
  ctx.textBaseline = "alphabetic";
}

function alignAt(x: number, geometry: AxisGeometry): CanvasTextAlign {
  if (x <= geometry.labelInset) return "left";
  if (x >= geometry.width - geometry.labelInset) return "right";
  return "center";
}

function labelX(x: number, align: CanvasTextAlign, geometry: AxisGeometry): number {
  if (align === "left") return geometry.labelInset;
  if (align === "right") return geometry.width - geometry.labelInset;
  return x;
}

interface Extent {
  left: number;
  right: number;
}

function textSpan(x: number, width: number, align: CanvasTextAlign): Extent {
  if (align === "left") return { left: x, right: x + width };
  if (align === "right") return { left: x - width, right: x };
  return { left: x - width / 2, right: x + width / 2 };
}

// Painted from the outer end inwards, so the label carrying the unit keeps its
// place and crowded neighbours drop out rather than printing on top of it.
class AxisPainter {
  private claimed = Infinity;

  constructor(
    private readonly surface: ChartSurface,
    private readonly range: Range,
    private readonly geometry: AxisGeometry,
  ) {}

  minorTick(value: number): void {
    const top = Math.max(this.geometry.tickTop, this.geometry.tickBottom - MINOR_TICK_LENGTH);
    this.tick(this.x(value), top);
  }

  majorTick(value: number, text: string): void {
    const x = this.x(value);
    this.tick(x, this.geometry.tickTop);
    const align = alignAt(x, this.geometry);
    this.label(text, labelX(x, align, this.geometry), align);
  }

  private label(text: string, x: number, align: CanvasTextAlign): void {
    const span = textSpan(x, this.measure(text), align);
    if (span.right + LABEL_GAP > this.claimed) return;
    this.claimed = span.left;
    axisLabel(this.surface, text, x, this.geometry.labelY, align);
  }

  private measure(text: string): number {
    this.surface.ctx.font = AXIS_FONT;
    return this.surface.ctx.measureText(text).width;
  }

  private x(value: number): number {
    return this.range.fractionOf(value) * this.geometry.width;
  }

  private tick(x: number, top: number): void {
    const { ctx, palette } = this.surface;
    ctx.strokeStyle = palette.tick;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, this.geometry.tickBottom);
    ctx.stroke();
  }
}

abstract class LabeledAxis {
  protected abstract format(value: number, last: boolean): string;

  draw(surface: ChartSurface, range: Range, geometry: AxisGeometry): void {
    const painter = new AxisPainter(surface, range, geometry);
    const step = range.step(Math.floor(geometry.width / LABEL_PITCH));
    range.ticks(step / MINORS_PER_MAJOR).forEach((value) => painter.minorTick(value));
    const outermostFirst = range.ticks(step).reverse();
    outermostFirst.forEach((value, i) => painter.majorTick(value, this.format(value, i === 0)));
  }
}

function trimmed(value: number, decimals: number): string {
  return String(Number(value.toFixed(decimals)));
}

export class FrequencyAxis extends LabeledAxis {
  protected format(hz: number, last: boolean): string {
    if (hz === 0) return "0";
    const kilohertz = trimmed(hz / 1000, 3);
    return last ? `${kilohertz} kHz` : `${kilohertz}k`;
  }
}

/** Labels seconds relative to the newest sample, so live sits at zero. */
export class TimeAxis extends LabeledAxis {
  protected format(seconds: number, last: boolean): string {
    const text = trimmed(seconds, 2);
    return last ? `${text} s` : text;
  }
}
