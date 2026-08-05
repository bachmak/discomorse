PRES.sceneTitle = (world) => {
  const { el, group } = PRES.svg;
  const layer = group(world, "layer lvl-title");

  el("circle", { cx: 0, cy: 0, r: 170, class: "stroke stroke-bold breathe" }, layer);

  const waves = Array.from({ length: 12 }, (_, i) => `q 13 ${i % 2 ? 22 : -22} 26 0`);
  new PRES.Arrow(layer, `M -530 0 ${waves.join(" ")} L -206 0`, { head: 13 });

  const spokes = [-32, 0, 32].map((deg) => {
    const rad = (deg * Math.PI) / 180;
    const dir = { x: Math.cos(rad), y: Math.sin(rad) };
    new PRES.Arrow(
      layer,
      PRES.svg.lineD(
        { x: dir.x * 184, y: dir.y * 184 },
        { x: dir.x * 336, y: dir.y * 336 },
      ),
      { head: 13 },
    );
    return dir;
  });

  drawFft(layer, spokes[0].x * 408, spokes[0].y * 408);
  drawPulses(layer, spokes[1].x * 418, spokes[1].y * 418);
  drawText(layer, spokes[2].x * 412, spokes[2].y * 412);
  drawMorse(layer, 0, 248, PRES.data.morse("discomorse"));

  return { el: layer, range: [1, 1] };
};

function drawFft(layer, x, y) {
  const g = PRES.svg.group(layer, "stroke");
  const heights = [10, 17, 12, 50, 20, 11, 7];
  heights.forEach((h, i) => {
    const bx = x + (i - 3) * 9;
    PRES.svg.el("line", { x1: bx, y1: y + 26, x2: bx, y2: y + 26 - h }, g);
  });
}

function drawPulses(layer, x, y) {
  const d = `M ${x - 24} ${y + 10} h6 v-20 h8 v20 h6 v-20 h22 v20 h6`;
  PRES.svg.el("path", { d, class: "stroke" }, layer);
}

function drawText(layer, x, y) {
  const g = PRES.svg.group(layer, "stroke");
  [[44, -12], [44, 0], [26, 12]].forEach(([w, dy]) => {
    PRES.svg.el("line", { x1: x - 22, y1: y + dy, x2: x - 22 + w, y2: y + dy }, g);
  });
}

function drawMorse(layer, cx, y, letters) {
  const g = PRES.svg.group(layer, "");
  g.setAttribute("opacity", 0.42);
  const dot = 4.6;
  const dash = 13;
  const widthOf = (sym) => [...sym].reduce((w, c) => w + (c === "." ? dot : dash) + 4.5, -4.5);
  const total = letters.reduce((w, sym) => w + widthOf(sym) + 10, -10);

  let x = cx - total / 2;
  for (const sym of letters) {
    for (const c of sym) {
      if (c === ".") PRES.svg.el("circle", { cx: x + dot / 2, cy: y, r: 2.3, class: "fill" }, g);
      else PRES.svg.el("line", { x1: x, y1: y, x2: x + dash, y2: y, class: "stroke" }, g);
      x += (c === "." ? dot : dash) + 4.5;
    }
    x += 10 - 4.5;
  }
}
