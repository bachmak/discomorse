PRES.sceneSystem = (world) => {
  const { el, group, circle, trimmed } = PRES.svg;
  const client = { x: 250, y: -62, r: 24 };

  const clientLayer = group(world, "layer lvl-system");
  circle(clientLayer, client.x, client.y, client.r, "stroke stroke-bold breathe");

  const activeTaps = PRES.graph.taps.filter((tap) => tap.active);
  const angles = [215, 182, 158, 136, 112];
  const curves = activeTaps.map((tap, i) => curveTo(tap.at, angles[i]));
  curves.push(uplink());

  const boxLayer = group(world, "layer lvl-system");
  box(boxLayer, -176, -42, 366, 84, "backend");
  box(boxLayer, 212, -102, 78, 80, "frontend");
  el("text", { x: 201, y: -30, class: "micro-label", text: "ws" }, boxLayer);

  const deployLayer = group(world, "layer lvl-system");
  container(deployLayer, -188, -54, 390, 108);
  container(deployLayer, 200, -114, 102, 104);
  container(deployLayer, 134, 84, 72, 74);
  circle(deployLayer, 170, 112, 16, "stroke breathe");
  el("text", { x: 170, y: 145, class: "box-label", "text-anchor": "middle", text: "caddy" }, deployLayer);
  link(deployLayer, { x: 10, y: 54 }, "8000", { x: 84, y: 75 });
  link(deployLayer, { x: 251, y: -10 }, "8080", { x: 220, y: 60 });
  new PRES.Arrow(deployLayer, trimmed({ x: 216, y: 192 }, { x: 170, y: 112 }, 0, 19), { cls: "stroke-hair" });
  el("text", { x: 214, y: 172, class: "micro-label", text: "443" }, deployLayer);

  function curveTo(from, angleDeg) {
    const rad = (angleDeg * Math.PI) / 180;
    const target = {
      x: client.x + client.r * Math.cos(rad),
      y: client.y + client.r * Math.sin(rad),
    };
    const dist = Math.hypot(target.x - from.x, target.y - from.y);
    const bow = 18 + dist * 0.12;
    const ctrl = { x: (from.x + target.x) / 2, y: (from.y + target.y) / 2 - bow };
    const toCtrl = Math.hypot(ctrl.x - from.x, ctrl.y - from.y);
    const start = {
      x: from.x + ((ctrl.x - from.x) / toCtrl) * 3,
      y: from.y + ((ctrl.y - from.y) / toCtrl) * 3,
    };
    const d = `M ${start.x} ${start.y} Q ${ctrl.x} ${ctrl.y} ${target.x} ${target.y}`;
    return new PRES.Arrow(clientLayer, d, { head: 2.3, cls: "dotted" });
  }

  function uplink() {
    const d = "M 245.8 -38.4 Q 40 120 -160 3.5";
    return new PRES.Arrow(clientLayer, d, { head: 2.8 });
  }

  function box(parent, x, y, w, h, label) {
    el("rect", { x, y, width: w, height: h, rx: 15, class: "stroke" }, parent);
    el("text", { x: x + 10, y: y + 12, class: "box-label", text: label }, parent);
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

  function link(parent, target, label, at) {
    const d = trimmed({ x: 170, y: 112 }, target, 19, 2);
    new PRES.Arrow(parent, d, { head: 3, cls: "stroke-hair" });
    el("text", { x: at.x, y: at.y, class: "micro-label", text: label }, parent);
  }

  let grown = false;
  return [
    {
      el: clientLayer,
      range: [7, 9],
      enter: () => {
        if (grown) return;
        grown = true;
        curves.forEach((curve, i) => curve.growFrom(250 + i * 110));
      },
    },
    { el: boxLayer, range: [8, 9] },
    { el: deployLayer, range: [9, 9] },
  ];
};
