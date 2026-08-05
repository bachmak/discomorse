PRES.Camera = class Camera {
  constructor(svg) {
    this.svg = svg;
    this.view = { cx: 0, cy: 0, w: 1200, h: 600 };
    this.cancel = null;
    window.addEventListener("resize", () => this.apply(this.view));
  }

  get aspect() {
    return Math.max(0.5, window.innerWidth / Math.max(1, window.innerHeight));
  }

  apply(view) {
    this.view = view;
    const w = Math.max(view.w, view.h * this.aspect);
    const h = w / this.aspect;
    this.svg.setAttribute(
      "viewBox",
      `${view.cx - w / 2} ${view.cy - h / 2} ${w} ${h}`,
    );
  }

  jumpTo(view) {
    if (this.cancel) this.cancel();
    this.apply(view);
  }

  flyTo(target) {
    if (this.cancel) this.cancel();
    const from = { ...this.view };
    const ratio = Math.max(target.w / from.w, from.w / target.w);
    const ms = Math.min(2000, 800 + 340 * Math.log2(ratio + 1));

    this.cancel = PRES.Tween.run({
      ms,
      step: (e) => this.apply(Camera.between(from, target, e)),
      done: () => {
        this.cancel = null;
      },
    });
  }

  static between(a, b, e) {
    const w = a.w * Math.pow(b.w / a.w, e);
    const zoomSpan = 1 / b.w - 1 / a.w;
    const f = Math.abs(zoomSpan) < 1e-9 ? e : (1 / w - 1 / a.w) / zoomSpan;
    return {
      cx: a.cx + (b.cx - a.cx) * f,
      cy: a.cy + (b.cy - a.cy) * f,
      w,
      h: a.h + (b.h - a.h) * e,
    };
  }
};
