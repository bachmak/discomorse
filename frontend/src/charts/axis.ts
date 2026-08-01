import type { Range } from "./ticks";

const AXIS_FONT = "12px ui-monospace, monospace";
const LABEL_COLOR = "rgba(148, 163, 184, 0.9)";
const TICK_COLOR = "rgba(34, 211, 238, 0.16)";
const CAPTION_BG = "rgba(8, 11, 17, 0.7)";
const CAPTION_PAD = 5;
const CAPTION_TOP = 8;
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
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  align: CanvasTextAlign = "center",
): void {
  ctx.fillStyle = LABEL_COLOR;
  ctx.font = AXIS_FONT;
  ctx.textAlign = align;
  ctx.textBaseline = "alphabetic";
  ctx.fillText(text, x, y);
}

export function axisCaption(ctx: CanvasRenderingContext2D, text: string, left = 8): void {
  ctx.font = AXIS_FONT;
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  const width = ctx.measureText(text).width + CAPTION_PAD * 2;
  ctx.fillStyle = CAPTION_BG;
  ctx.beginPath();
  ctx.roundRect(left, CAPTION_TOP, width, 11 + CAPTION_PAD * 2, 4);
  ctx.fill();
  ctx.fillStyle = LABEL_COLOR;
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

class AxisPainter {
  constructor(
    private readonly ctx: CanvasRenderingContext2D,
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
    axisLabel(this.ctx, text, labelX(x, align, this.geometry), this.geometry.labelY, align);
  }

  private x(value: number): number {
    return this.range.fractionOf(value) * this.geometry.width;
  }

  private tick(x: number, top: number): void {
    this.ctx.strokeStyle = TICK_COLOR;
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(x, top);
    this.ctx.lineTo(x, this.geometry.tickBottom);
    this.ctx.stroke();
  }
}

abstract class LabeledAxis {
  protected abstract format(value: number, last: boolean): string;

  draw(ctx: CanvasRenderingContext2D, range: Range, geometry: AxisGeometry): void {
    const painter = new AxisPainter(ctx, range, geometry);
    const step = range.step(Math.floor(geometry.width / LABEL_PITCH));
    range.ticks(step / MINORS_PER_MAJOR).forEach((value) => painter.minorTick(value));
    const labelled = range.ticks(step);
    const last = labelled.length - 1;
    labelled.forEach((value, i) => painter.majorTick(value, this.format(value, i === last)));
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
