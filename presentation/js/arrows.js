PRES.Arrow = class Arrow {
  constructor(parent, d, { head = 3.2, cls = "" } = {}) {
    this.group = PRES.svg.group(parent, `arrow ${cls}`.trim());
    this.shaft = PRES.svg.el("path", { d, class: "shaft" }, this.group);
    this.head = PRES.svg.el(
      "path",
      { d: `M ${-head} ${-head} L 0 0 L ${-head} ${head}`, class: "head" },
      this.group,
    );
    this.len = this.shaft.getTotalLength();
    this.flipped = 0;
    this.cancel = null;
    this.setFlip(0);
  }

  pointAt(l) {
    return this.shaft.getPointAtLength(Math.max(0, Math.min(this.len, l)));
  }

  setFlip(e) {
    this.flipped = e;
    const l = this.len * (1 - e);
    const before = this.pointAt(l - 0.5);
    const after = this.pointAt(l + 0.5);
    const tangent = (Math.atan2(after.y - before.y, after.x - before.x) * 180) / Math.PI;
    const p = this.pointAt(l);
    this.head.setAttribute(
      "transform",
      `translate(${p.x} ${p.y}) rotate(${tangent + 180 * e})`,
    );
  }

  schedule(delay, ms, ease, makeStep) {
    if (this.cancel) this.cancel();
    const timer = setTimeout(() => {
      this.cancel = PRES.Tween.run({ ms, ease, step: makeStep() });
    }, delay);
    this.cancel = () => clearTimeout(timer);
  }

  flip(reversed, delay = 0) {
    this.finishDraw();
    this.finishGrow();
    const target = reversed ? 1 : 0;
    this.schedule(delay, 520, PRES.ease.inOutCubic, () => {
      const start = this.flipped;
      return (e) => this.setFlip(start + (target - start) * e);
    });
  }

  drawIn(delay = 0) {
    this.drawing = true;
    this.shaft.setAttribute("stroke-dasharray", `${this.len} ${this.len}`);
    this.shaft.setAttribute("stroke-dashoffset", this.len);
    this.head.setAttribute("opacity", 0);
    this.schedule(delay, 650, PRES.ease.outCubic, () => (e) => {
      this.shaft.setAttribute("stroke-dashoffset", this.len * (1 - e));
      this.head.setAttribute("opacity", Math.max(0, (e - 0.7) / 0.3));
      if (e === 1) this.drawing = false;
    });
  }

  finishDraw() {
    if (!this.drawing) return;
    this.drawing = false;
    this.shaft.setAttribute("stroke-dashoffset", 0);
    this.head.setAttribute("opacity", 1);
  }

  growFrom(delay = 0) {
    this.growing = true;
    this.group.setAttribute("opacity", 0);
    this.schedule(delay, 600, PRES.ease.outCubic, () => (e) => {
      this.group.setAttribute("opacity", e);
      this.setFlip(1 - e);
      if (e === 1) this.growing = false;
    });
  }

  finishGrow() {
    if (!this.growing) return;
    this.growing = false;
    this.group.setAttribute("opacity", 1);
    this.setFlip(0);
  }
};
