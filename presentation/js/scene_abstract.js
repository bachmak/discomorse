PRES.sceneAbstract = (world) => {
  const { el, group, circle, trimmed } = PRES.svg;
  const R = 6;
  const nodes = {
    a: { x: -56, y: 0 },
    b: { x: -30, y: 0 },
    c: { x: -2, y: -15 },
    d: { x: -2, y: 15 },
    e: { x: 26, y: 0 },
    f: { x: 52, y: 0 },
  };

  const graph = group(world, "layer lvl-abstract");
  const arrows = [
    new PRES.Arrow(graph, "M -72 0 L -63.5 0", { head: 2.6 }),
    edge(graph, nodes.a, nodes.b),
    edge(graph, nodes.b, nodes.c),
    edge(graph, nodes.b, nodes.d),
    edge(graph, nodes.c, nodes.e),
    edge(graph, nodes.d, nodes.e),
    edge(graph, nodes.e, nodes.f),
    new PRES.Arrow(graph, "M 59.5 0 L 68 0", { head: 2.6 }),
  ];
  for (const [i, n] of Object.values(nodes).entries()) {
    const ring = circle(graph, n.x, n.y, R, "stroke breathe");
    ring.style.animationDelay = `${-i * 0.9}s`;
  }

  const code = group(world, "layer code");
  const lineHeight = 0.345;
  const top = nodes.b.y - (PRES.data.code.length - 1) * lineHeight * 0.5;
  PRES.data.code.forEach((runs, i) => {
    const text = el(
      "text",
      { x: nodes.b.x - 5.35, y: top + i * lineHeight, "font-size": 0.23, "xml:space": "preserve" },
      code,
    );
    for (const [kind, chunk] of runs) {
      el("tspan", { class: `tok-${kind}`, text: chunk }, text);
    }
  });

  function edge(parent, from, to) {
    return new PRES.Arrow(parent, trimmed(from, to, R + 1.2, R + 1.2), { head: 2.6 });
  }

  let drawn = false;
  return [
    {
      el: graph,
      on: ["pipeline", "interface"],
      enter: () => {
        if (drawn) return;
        drawn = true;
        arrows.forEach((arrow, i) => arrow.drawIn(i * 90));
      },
    },
    { el: code, on: ["interface"] },
  ];
};
