PRES.sceneSystem = (world) => {
  const { el, group, circle, trimmed } = PRES.svg;
  const client = { x: 250, y: -62, r: 24 };
  const backend = { x: -176, y: -42, w: 366, h: 84 };
  const rimGap = 2.5;

  const clientLayer = group(world, "layer lvl-system");
  circle(clientLayer, client.x, client.y, client.r, "stroke stroke-bold breathe");

  const pollLayer = group(world, "layer lvl-system");
  const activeTaps = PRES.graph.taps.filter((tap) => tap.active);
  const angles = [215, 182, 158, 136, 112];
  const curves = activeTaps.map((tap, i) => pollCurve(tap.at, angles[i]));
  curves.push(inputPull());

  const boxLayer = group(world, "layer lvl-system");
  box(boxLayer, backend, "backend");
  box(boxLayer, { x: 212, y: -102, w: 78, h: 80 }, "frontend");

  const wsLayer = group(world, "layer lvl-system");
  const wsLinks = [
    wsLink(rimPoint(190), edgeOfBackend(-24), 6, "dotted flow-back"),
    wsLink(edgeOfBackend(-8), rimPoint(160), -6),
  ];
  el("text", { x: 207, y: -34, class: "micro-label", text: "ws" }, wsLayer);

  const deployLayer = group(world, "layer lvl-system");
  container(deployLayer, -188, -54, 390, 108);
  container(deployLayer, 200, -114, 102, 104);
  container(deployLayer, 134, 84, 72, 74);
  circle(deployLayer, 170, 112, 16, "stroke breathe");
  el("text", { x: 170, y: 145, class: "box-label", "text-anchor": "middle", text: "caddy" }, deployLayer);
  route(deployLayer, { x: 10, y: 54 }, "8000", { x: 84, y: 75 });
  route(deployLayer, { x: 251, y: -10 }, "8080", { x: 220, y: 60 });
  new PRES.Arrow(deployLayer, trimmed({ x: 216, y: 192 }, { x: 170, y: 112 }, 0, 19), { cls: "stroke-hair" });
  el("text", { x: 214, y: 172, class: "micro-label", text: "443" }, deployLayer);

  function rimPoint(angleDeg) {
    const rad = (angleDeg * Math.PI) / 180;
    return {
      x: client.x + (client.r + rimGap) * Math.cos(rad),
      y: client.y + (client.r + rimGap) * Math.sin(rad),
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

  function edgeOfBackend(y) {
    return { x: backend.x + backend.w + 2, y };
  }

  function wsLink(from, to, bow, cls = "") {
    const d = arcD(from, bowCtrl(from, to, bow), to);
    return new PRES.Arrow(wsLayer, d, { head: 2.8, cls });
  }

  function box(parent, rect, label) {
    el("rect", { x: rect.x, y: rect.y, width: rect.w, height: rect.h, rx: 15, class: "stroke" }, parent);
    el("text", { x: rect.x + 10, y: rect.y + 12, class: "box-label", text: label }, parent);
  }

  function container(parent, x, y, w, h) {
    el("rect", { x, y, width: w, height: h, rx: 18, class: "stroke stroke-soft" }, parent);
    for (let i = 0; i < 3; i += 1) {
      el(
        "rect",
        { x: x + w - 10 - i * 5.4, y: y + 6, width: 3.2, height: 3.2, class: "stroke stroke-soft" },
        parent,
      );
    }
  }

  function route(parent, target, label, at) {
    const d = trimmed({ x: 170, y: 112 }, target, 19, 2);
    new PRES.Arrow(parent, d, { head: 3, cls: "stroke-hair" });
    el("text", { x: at.x, y: at.y, class: "micro-label", text: label }, parent);
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
