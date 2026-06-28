const AXIS_FONT = "12px ui-monospace, monospace";
const LABEL_COLOR = "rgba(148, 163, 184, 0.9)";
const TICK_COLOR = "rgba(34, 211, 238, 0.16)";
const CAPTION_BG = "rgba(8, 11, 17, 0.7)";
const CAPTION_PAD = 5;
const CAPTION_TOP = 8;

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

function tickGuide(ctx: CanvasRenderingContext2D, x: number, top: number, bottom: number): void {
  ctx.strokeStyle = TICK_COLOR;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, top);
  ctx.lineTo(x, bottom);
  ctx.stroke();
}

function linearTicks(max: number, step: number): number[] {
  const count = Math.round(max / step);
  return Array.from({ length: count + 1 }, (_unused, i) => i * step);
}

function edgeAlign(index: number, count: number): CanvasTextAlign {
  if (index === 0) return "left";
  if (index === count - 1) return "right";
  return "center";
}

function labelX(x: number, align: CanvasTextAlign, geometry: AxisGeometry): number {
  if (align === "left") return geometry.labelInset;
  if (align === "right") return geometry.width - geometry.labelInset;
  return x;
}

abstract class LabeledAxis {
  constructor(
    protected readonly max: number,
    protected readonly step: number,
  ) {}

  protected abstract format(value: number): string;

  draw(ctx: CanvasRenderingContext2D, geometry: AxisGeometry): void {
    const ticks = linearTicks(this.max, this.step);
    ticks.forEach((value, index) => {
      const x = (value / this.max) * geometry.width;
      tickGuide(ctx, x, geometry.tickTop, geometry.tickBottom);
      const align = edgeAlign(index, ticks.length);
      axisLabel(ctx, this.format(value), labelX(x, align, geometry), geometry.labelY, align);
    });
  }
}

export class FrequencyAxis extends LabeledAxis {
  protected format(hz: number): string {
    if (hz === 0) return "0";
    const kilohertz = hz / 1000;
    return hz === this.max ? `${kilohertz} kHz` : `${kilohertz}k`;
  }
}

export class TimeAxis extends LabeledAxis {
  protected format(ms: number): string {
    return ms === this.max ? `${ms} ms` : `${ms}`;
  }
}
