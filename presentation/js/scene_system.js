PRES.sceneSystem = (world) => {
  const { el, group, circle, trimmed } = PRES.svg;

  const BOX = { w: 200, h: 112 };
  const PAD = 16;
  const GAP = 64;
  const NODE_R = 32;
  const RIM_GAP = 2.5;
  const STRIDE = { x: BOX.w + 2 * PAD + GAP, y: BOX.h + 2 * PAD + GAP };

  class Block {
    constructor(cx, cy, label) {
      this.cx = cx;
      this.cy = cy;
      this.label = label;
    }

    get center() {
      return { x: this.cx, y: this.cy };
    }

    get rect() {
      return { x: this.cx - BOX.w / 2, y: this.cy - BOX.h / 2, w: BOX.w, h: BOX.h };
    }

    get shell() {
      const r = this.rect;
      return { x: r.x - PAD, y: r.y - PAD, w: r.w + 2 * PAD, h: r.h + 2 * PAD };
    }

    get rightEdge() {
      return this.cx + BOX.w / 2;
    }

    get shellFoot() {
      return { x: this.cx, y: this.cy + BOX.h / 2 + PAD };
    }

    get shellHead() {
      return { x: this.cx, y: this.cy - BOX.h / 2 - PAD };
    }
  }

  const frontend = new Block(250, -62, "frontend");
  const backend = new Block(frontend.cx - STRIDE.x, frontend.cy, "backend");
  const caddy = new Block(frontend.cx - STRIDE.x / 2, frontend.cy + STRIDE.y, "caddy");

  const clientLayer = group(world, "layer lvl-system");
  circle(clientLayer, frontend.cx, frontend.cy, NODE_R, "stroke stroke-bold breathe");

  const pollLayer = group(world, "layer lvl-system");
  const activeTaps = PRES.graph.taps.filter((tap) => tap.active);
  const angles = [215, 182, 158, 136, 112];
  const curves = activeTaps.map((tap, i) => pollCurve(tap.at, angles[i]));
  curves.push(inputPull());

  const boxLayer = group(world, "layer lvl-system");
  drawBox(boxLayer, backend);
  drawBox(boxLayer, frontend);

  const wsLayer = group(world, "layer lvl-system");
  const wsLinks = [
    wsLink(rimPoint(190), backendPort(-8), 8, "dotted flow-back"),
    wsLink(backendPort(8), rimPoint(170), -8),
  ];
  el(
    "text",
    { x: (backend.rightEdge + frontend.cx - NODE_R) / 2, y: frontend.cy + 2, class: "micro-label", text: "ws" },
    wsLayer,
  );

  const deployLayer = group(world, "layer lvl-system");
  [backend, frontend, caddy].forEach((block) => drawShell(deployLayer, block));
  drawBox(deployLayer, caddy);
  circle(deployLayer, caddy.cx, caddy.cy, NODE_R, "stroke stroke-bold breathe");
  route(deployLayer, backend, "8000");
  route(deployLayer, frontend, "8080");
  ingress(deployLayer, "443");

  function rimPoint(angleDeg) {
    const rad = (angleDeg * Math.PI) / 180;
    return {
      x: frontend.cx + (NODE_R + RIM_GAP) * Math.cos(rad),
      y: frontend.cy + (NODE_R + RIM_GAP) * Math.sin(rad),
    };
  }

  function nudged(point, toward, by) {
    const len = Math.hypot(toward.x - point.x, toward.y - point.y);
    return {
      x: point.x + ((toward.x - point.x) / len) * by,
      y: point.y + ((toward.y - point.y) / len) * by,
    };
  }

  function bowCtrl(from, to, bow) {
    return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - bow };
  }

  function arcD(from, ctrl, to) {
    return `M ${from.x} ${from.y} Q ${ctrl.x} ${ctrl.y} ${to.x} ${to.y}`;
  }

  function pollCurve(tap, angleDeg) {
    const start = rimPoint(angleDeg);
    const bow = 18 + Math.hypot(start.x - tap.x, start.y - tap.y) * 0.12;
    const ctrl = bowCtrl(start, tap, bow);
    const tip = nudged(tap, ctrl, 3);
    return new PRES.Arrow(pollLayer, arcD(start, ctrl, tip), { head: 2.3, cls: "dotted flow-back" });
  }

  function inputPull() {
    const port = PRES.graph.inputPort;
    const tip = rimPoint(100);
    const d = `M ${port.x} ${port.y} C -235 50, 60 120, ${tip.x} ${tip.y}`;
    return new PRES.Arrow(pollLayer, d, { head: 2.8 });
  }

  function backendPort(dy) {
    return { x: backend.rightEdge + 2, y: backend.cy + dy };
  }

  function wsLink(from, to, bow, cls = "") {
    const d = arcD(from, bowCtrl(from, to, bow), to);
    return new PRES.Arrow(wsLayer, d, { head: 2.8, cls });
  }

  function drawBox(parent, block) {
    const r = block.rect;
    el("rect", { x: r.x, y: r.y, width: r.w, height: r.h, rx: 15, class: "stroke" }, parent);
    el("text", { x: r.x + 12, y: r.y + 15, class: "box-label", text: block.label }, parent);
  }

  function drawShell(parent, block) {
    const r = block.shell;
    el("rect", { x: r.x, y: r.y, width: r.w, height: r.h, rx: 20, class: "stroke stroke-soft" }, parent);
    for (let i = 0; i < 3; i += 1) {
      el(
        "rect",
        { x: r.x + r.w - 14 - i * 7, y: r.y + 8, width: 4, height: 4, class: "stroke stroke-soft" },
        parent,
      );
    }
  }

  function route(parent, block, label) {
    const foot = block.shellFoot;
    new PRES.Arrow(parent, trimmed(caddy.center, foot, NODE_R + 3, 2), { head: 3, cls: "stroke-hair" });
    el("text", { ...inGap(block), class: "micro-label", text: label }, parent);
  }

  function inGap(block) {
    const y = (block.shellFoot.y + caddy.shellHead.y) / 2;
    const travelled = (caddy.cy - y) / (caddy.cy - block.shellFoot.y);
    return {
      x: caddy.cx + (block.cx - caddy.cx) * travelled + Math.sign(block.cx - caddy.cx) * 22,
      y: y + 2,
    };
  }

  function ingress(parent, label) {
    const from = { x: caddy.cx, y: caddy.shellFoot.y + 26 };
    new PRES.Arrow(parent, trimmed(from, caddy.center, 0, NODE_R + 3), { head: 3, cls: "stroke-hair" });
    el("text", { x: from.x + 20, y: from.y - 16, class: "micro-label", text: label }, parent);
  }

  let polled = false;
  let linked = false;
  return [
    { el: clientLayer, range: [7, 9] },
    {
      el: pollLayer,
      range: [7, 7],
      enter: () => {
        if (polled) return;
        polled = true;
        curves.forEach((curve, i) => curve.growFrom(250 + i * 110));
      },
    },
    { el: boxLayer, range: [8, 9] },
    {
      el: wsLayer,
      range: [8, 9],
      enter: () => {
        if (linked) return;
        linked = true;
        wsLinks.forEach((wsArrow, i) => wsArrow.growFrom(300 + i * 200));
      },
    },
    { el: deployLayer, range: [9, 9] },
  ];
};
