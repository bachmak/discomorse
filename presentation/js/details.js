PRES.DetailView = class DetailView {
  constructor(world, stage, center) {
    const { el, group, circle } = PRES.svg;
    this.stage = stage;
    this.cam = { cx: center.x, cy: center.y + 0.8, w: 45, h: 26 };
    const g = group(world, "detail off");
    this.el = g;

    this.backdrop = circle(g, center.x, center.y, 34, "");
    this.backdrop.setAttribute("fill", "#fff");
    this.backdrop.setAttribute("opacity", 0.985);

    circle(g, center.x, center.y, 7.6, "stroke detail-ring");
    el("text", { x: center.x, y: center.y - 3.7, class: "detail-type", text: stage.tIn }, g);
    el("text", { x: center.x, y: center.y + 5.6, class: "detail-type", text: stage.tOut }, g);
    this.drawArity(center);

    el("line", { x1: center.x, y1: center.y + 7.6, x2: center.x, y2: center.y + 8.9, class: "stroke stroke-hair" }, g);
    circle(g, center.x, center.y + 9.9, 0.6, "fill breathe");
    el("text", { x: center.x, y: center.y + 12.4, class: "detail-impl", text: stage.impl }, g);
  }

  drawArity(center) {
    const { el, circle } = PRES.svg;
    const count = this.stage.oneToOne ? 1 : 3;
    for (const side of [-1, 1]) {
      for (let i = 0; i < count; i += 1) {
        const offset = (i - (count - 1) / 2) * 1.2;
        circle(this.el, center.x + side * 4.4 + offset, center.y + 0.6, 0.3, "fill");
      }
    }
    el("line", { x1: center.x, y1: center.y - 0.9, x2: center.x, y2: center.y + 1.7, class: "stroke stroke-hair" }, this.el);
    el(
      "path",
      {
        d: "M -0.7 -0.7 L 0 0 L 0.7 -0.7",
        class: "stroke stroke-hair",
        transform: `translate(${center.x} ${center.y + 2.1})`,
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
