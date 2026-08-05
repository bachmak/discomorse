PRES.PathGlyph = class PathGlyph {
  constructor(paths, weight = 1) {
    this.paths = paths;
    this.weight = weight;
  }

  render(parent, stroke) {
    for (const d of this.paths) {
      PRES.svg.el("path", { d, class: "stroke", style: `stroke-width:${stroke * this.weight}` }, parent);
    }
  }
};

PRES.TextGlyph = class TextGlyph {
  constructor(label) {
    this.label = label;
  }

  render(parent) {
    PRES.svg.el("text", { x: 0, y: 3.1, class: "glyph-text", text: this.label }, parent);
  }
};

PRES.glyphs = (() => {
  const { PathGlyph, TextGlyph } = PRES;
  const BOX = 10;
  const BASE = 5;
  const HI = -3.4;
  const LO = 3.4;

  const bins = [
    [-9, 2.2], [-7, 3.8], [-5, 2.6], [-3, 5.6], [-1, 3.2],
    [1, 9.6], [3, 4.0], [5, 2.4], [7, 4.4], [9, 2.0],
  ];

  const comb = (kept) => kept.map(([x, h]) => `M ${x} ${BASE} V ${BASE - h}`);
  const inBand = ([x]) => Math.abs(x) <= 5;
  const bracket = (x, tip) => `M ${x + tip} -4.6 H ${x} V ${BASE}`;

  const polyline = (points) => points.map(([x, y], i) => `${i ? "L" : "M"} ${x} ${y}`).join(" ");

  function square(edges) {
    const parts = [`M -10 ${LO}`];
    edges.forEach((x, i) => parts.push(`H ${x}`, `V ${i % 2 ? LO : HI}`));
    return [...parts, "H 10"].join(" ");
  }

  const dash = (from, to) => `M ${from} 0 H ${to}`;
  const dot = (x) => `M ${x} 0 H ${x + 0.02}`;
  const rule = (to, y) => `M -8.5 ${y} H ${to}`;

  const shapes = {
    wave: new PathGlyph([
      "M -10 0 C -8.7 -4.6 -6.3 -4.6 -5 0 C -3.7 4.6 -1.3 4.6 0 0"
      + " C 1.3 -4.6 3.7 -4.6 5 0 C 6.3 4.6 8.7 4.6 10 0",
    ]),
    spectrum: new PathGlyph([`M -10 ${BASE} H 10`, ...comb(bins)]),
    band: new PathGlyph([
      `M -10 ${BASE} H 10`, ...comb(bins.filter(inBand)), bracket(-6.4, 1.4), bracket(6.4, -1.4),
    ]),
    peak: new PathGlyph(["M -10 3.6 H -2.2 L 0 -5 L 2.2 3.6 H 10"]),
    noise: new PathGlyph([polyline([
      [-10, 0.6], [-8, -2.8], [-6, 2.4], [-4, -3.4], [-2, 1.4], [0, -2.2],
      [2, 3.2], [4, -2.6], [6, 1.0], [8, -3.2], [10, 2.6],
    ])]),
    mixed: new PathGlyph([polyline([
      [-10, 3.6], [-8.6, 2.2], [-7.2, 4.0], [-5.8, 2.4], [-4.4, 3.8], [-3, 2.6],
      [-1.6, 3.6], [-0.8, 1.8], [0, -5], [0.8, 1.6], [1.6, 3.4], [3, 2.4],
      [4.4, 3.8], [5.8, 2.2], [7.2, 4.0], [8.6, 2.6], [10, 3.6],
    ])]),
    pulses: new PathGlyph([square([-8.4, -6.6, -5.6, -5.0, -2.2, 1.4, 2.6, 3.2, 5.0, 8.0])]),
    clean: new PathGlyph([square([-7.6, -5.2, -2.8, 1.8, 4.2, 6.6])]),
    morse: new PathGlyph([dot(-8.5), dash(-6, -1), dot(1.5), dash(4, 9)], 2.6),
    letters: new TextGlyph("ABCD"),
    text: new PathGlyph([rule(8.5, -3.2), rule(8.5, 0), rule(2.5, 3.2)]),
  };

  function draw(parent, name, at, { size, stroke }) {
    const k = size / BOX;
    const g = PRES.svg.group(parent, "glyph");
    g.setAttribute("transform", `translate(${at.x} ${at.y}) scale(${k})`);
    shapes[name].render(g, stroke / k);
    return g;
  }

  return { draw };
})();
