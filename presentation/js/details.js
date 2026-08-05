PRES.DetailView = class DetailView {
  constructor(world, stage, center) {
    this.stage = stage;
    this.center = center;
    this.el = PRES.svg.group(world, "detail off");
    this.cam = { cx: center.x + 12, cy: center.y + 1.4, w: 54, h: 30 };
    this.backdrop = this.drawBackdrop();
    this.drawRing();
    this.drawArity();
    this.drawImpl();
    this.drawNotes();
  }

  drawBackdrop() {
    const disc = PRES.svg.circle(this.el, this.center.x, this.center.y, 56, "");
    disc.setAttribute("fill", "#fff");
    disc.setAttribute("opacity", 0.985);
    return disc;
  }

  drawRing() {
    const { el, circle } = PRES.svg;
    const { x, y } = this.center;
    circle(this.el, x, y, 7.6, "stroke detail-ring");
    el("text", { x, y: y - 3.7, class: "detail-type", text: this.stage.tIn }, this.el);
    el("text", { x, y: y + 5.6, class: "detail-type", text: this.stage.tOut }, this.el);
  }

  drawImpl() {
    const { el, circle } = PRES.svg;
    const { x, y } = this.center;
    el("line", { x1: x, y1: y + 7.6, x2: x, y2: y + 8.9, class: "stroke stroke-hair" }, this.el);
    circle(this.el, x, y + 9.9, 0.6, "fill breathe");
    el("text", { x, y: y + 12.4, class: "detail-impl", text: this.stage.impl }, this.el);
  }

  drawNotes() {
    const { el, circle } = PRES.svg;
    const { notes } = this.stage;
    notes.forEach((note, i) => {
      const y = this.center.y + (i - (notes.length - 1) / 2) * 2.6;
      circle(this.el, this.center.x + 10.4, y - 0.35, 0.22, "fill note-dot");
      el("text", { x: this.center.x + 11.7, y, class: "detail-note", text: note }, this.el);
    });
  }

  drawArity() {
    const { el, circle } = PRES.svg;
    const { x, y } = this.center;
    const count = this.stage.oneToOne ? 1 : 3;
    for (const side of [-1, 1]) {
      for (let i = 0; i < count; i += 1) {
        const offset = (i - (count - 1) / 2) * 1.2;
        circle(this.el, x + side * 4.4 + offset, y + 0.6, 0.3, "fill");
      }
    }
    el("line", { x1: x, y1: y - 0.9, x2: x, y2: y + 1.7, class: "stroke stroke-hair" }, this.el);
    el(
      "path",
      {
        d: "M -0.7 -0.7 L 0 0 L 0.7 -0.7",
        class: "stroke stroke-hair",
        transform: `translate(${x} ${y + 2.1})`,
      },
      this.el,
    );
  }
};

PRES.details = (() => {
  const views = {};
  let openId = null;

  function build(world) {
    for (const stage of PRES.data.stages) {
      views[stage.id] = new PRES.DetailView(world, stage, PRES.graph.nodes[stage.id]);
      views[stage.id].backdrop.addEventListener("click", close);
    }
  }

  function open(id) {
    if (openId) views[openId].el.classList.add("off");
    openId = id;
    document.body.classList.add("detail-open");
    const view = views[id];
    view.el.classList.remove("off");
    PRES.camera.flyTo(view.cam);
    PRES.deck.setHeader(view.stage.name);
  }

  function close() {
    if (!openId) return;
    views[openId].el.classList.add("off");
    openId = null;
    document.body.classList.remove("detail-open");
    PRES.deck.restore();
  }

  function step(delta) {
    const order = PRES.data.stages.map((stage) => stage.id);
    const next = order[(order.indexOf(openId) + delta + order.length) % order.length];
    open(next);
  }

  function handleKey(key) {
    if (!openId) return false;
    if (key === "Escape" || key === " " || key === "Enter") close();
    else if (key === "ArrowRight" || key === "ArrowDown") step(1);
    else if (key === "ArrowLeft" || key === "ArrowUp") step(-1);
    return true;
  }

  return { build, open, close, handleKey, isOpen: () => openId !== null };
})();
