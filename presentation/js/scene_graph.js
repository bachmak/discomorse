PRES.sceneGraph = (world) => {
  const { el, group, circle, trimmed, lineD } = PRES.svg;
  const R = 6;
  const UP = { x: 0.5, y: -0.866 };
  const DOWN = { x: 0.5, y: 0.866 };

  const nodes = {
    sa: { x: -128, y: 0 }, sl: { x: -92, y: 0 },
    cs: { x: -48, y: -17 }, ne: { x: -48, y: 17 },
    kd: { x: 4, y: 0 }, kb: { x: 40, y: 0 }, td: { x: 76, y: 0 },
    sd: { x: 112, y: 0 }, tc: { x: 148, y: 0 },
  };
  const fork = { x: -72, y: 0 };
  const zip = { x: -14, y: 0 };
  const inputTail = { x: -160, y: 0 };
  const inputPort = { x: nodes.sa.x - R - 1.5, y: 0 };

  const graph = group(world, "layer lvl-graph");
  const inputEdge = new PRES.Arrow(graph, lineD(inputTail, inputPort));
  const edges = [
    inputEdge,
    new PRES.Arrow(graph, trimmed(nodes.sa, nodes.sl, R + 1.5, R + 1.5)),
    forkEdge(nodes.cs), forkEdge(nodes.ne),
    zipEdge(nodes.cs), zipEdge(nodes.ne),
    new PRES.Arrow(graph, "M -11 0 L -3.5 0"),
    new PRES.Arrow(graph, trimmed(nodes.kd, nodes.kb, R + 1.5, R + 1.5)),
    new PRES.Arrow(graph, trimmed(nodes.kb, nodes.td, R + 1.5, R + 1.5)),
    new PRES.Arrow(graph, trimmed(nodes.td, nodes.sd, R + 1.5, R + 1.5)),
    new PRES.Arrow(graph, trimmed(nodes.sd, nodes.tc, R + 1.5, R + 1.5)),
    new PRES.Arrow(graph, "M 155.5 0 L 184 0"),
  ];
  circle(graph, zip.x, zip.y, 1.5, "fill");

  PRES.data.stages.forEach((stage, i) => {
    const n = nodes[stage.id];
    const g = group(graph, "node");
    g.dataset.stage = stage.id;
    const core = circle(g, n.x, n.y, R, "core breathe");
    core.style.animationDelay = `${-i * 0.7}s`;
    circle(g, n.x, n.y, R + 1.6, "halo");
    el("text", { x: n.x, y: n.y + R + 5.5, class: "node-label", text: stage.name }, g);
    core.addEventListener("click", () => PRES.details.open(stage.id));
  });

  const streamLayer = group(world, "layer lvl-graph");
  const taps = [
    { ch: "spectrums", at: { x: -110, y: 0 }, dir: UP },
    { ch: "limited_spectrums", at: fork, dir: UP },
    { ch: "carrier_samples", at: onZipLine(nodes.cs), dir: UP },
    { ch: "noise_samples", at: onZipLine(nodes.ne), dir: DOWN },
    { ch: "raw_tones", at: { x: 22, y: 0 }, dir: UP },
    { ch: "debounced_tones", at: { x: 58, y: 0 }, dir: UP },
    { ch: "morse_elements", at: { x: 94, y: 0 }, dir: UP },
    { ch: "decoded_symbols", at: { x: 130, y: 0 }, dir: UP },
    { ch: "corrected_text", at: { x: 170, y: 0 }, dir: UP },
  ];
  for (const tap of taps) {
    tap.active = PRES.data.subscribed.has(tap.ch);
    tap.dot = circle(streamLayer, tap.at.x, tap.at.y, 1.9, "tap");
    tap.tip = { x: tap.at.x + tap.dir.x * 24, y: tap.at.y + tap.dir.y * 24 };
    const start = { x: tap.at.x + tap.dir.x * 3.4, y: tap.at.y + tap.dir.y * 3.4 };
    tap.arrow = new PRES.Arrow(streamLayer, lineD(start, tap.tip), { head: 2.4, cls: "dotted" });
  }

  const glyphSpots = {
    in: { x: -147, y: 14 },
    sa: { x: -116, y: -14 },
    sl: { x: -81, y: 14 },
    cs: { x: -48, y: -30 },
    ne: { x: -48, y: 30 },
    zip: { x: -17, y: -14 },
    kd: { x: 24, y: 14 },
    kb: { x: 52, y: -14 },
    td: { x: 94, y: 14 },
    sd: { x: 124, y: -14 },
    tc: { x: 170, y: 14 },
  };
  const glyphNames = {
    ...Object.fromEntries(PRES.data.stages.map((s) => [s.id, s.glyphs.out])),
    in: PRES.data.byId.sa.glyphs.in,
    zip: PRES.data.byId.kd.glyphs.in,
  };

  const glyphLayer = group(world, "layer lvl-graph");
  Object.entries(glyphSpots).forEach(([id, at], i) => {
    const g = PRES.glyphs.draw(glyphLayer, glyphNames[id], at, { size: 7, stroke: 0.5 });
    g.style.transitionDelay = `${i * 70}ms`;
  });

  function forkEdge(target) {
    const d = trimmed(fork, target, 0, R + 1.5);
    return new PRES.Arrow(graph, `M -84.5 0 L ${fork.x} ${fork.y} ${d.slice(d.indexOf("L"))}`);
  }

  function zipEdge(source) {
    return new PRES.Arrow(graph, trimmed(source, zip, R + 1.5, 3));
  }

  function onZipLine(source) {
    return {
      x: source.x + (zip.x - source.x) * 0.45,
      y: source.y + (zip.y - source.y) * 0.45,
    };
  }

  const allArrows = () => [...edges, ...taps.map((t) => t.arrow)];

  function flipAll(reversed) {
    const sorted = allArrows().sort((p, q) => {
      const px = p.pointAt(p.len).x;
      const qx = q.pointAt(q.len).x;
      return reversed ? qx - px : px - qx;
    });
    sorted.forEach((arrow, i) => arrow.flip(reversed, i * 45));
  }

  let edgesDrawn = false;
  let streamsGrown = false;

  PRES.graph = { nodes, taps, inputPort, R, flipAll };

  return [
    { el: glyphLayer, range: [4, 7] },
    {
      el: graph,
      range: [4, 7],
      enter: () => {
        if (edgesDrawn) return;
        edgesDrawn = true;
        edges.forEach((edge, i) => edge.drawIn(i * 70));
      },
      update: (n) => {
        document.getElementById("stage").classList.toggle("interactive", n >= 4 && n <= 7);
        inputEdge.group.classList.toggle("gone", n >= 7);
      },
    },
    {
      el: streamLayer,
      range: [5, 7],
      enter: () => {
        if (streamsGrown) return;
        streamsGrown = true;
        taps.forEach((tap, i) => tap.arrow.growFrom(150 + i * 80));
      },
      update: (n) => {
        for (const tap of taps) {
          tap.dot.classList.toggle("live", n >= 7 && tap.active);
          tap.dot.classList.toggle("faint", n >= 7 && !tap.active);
          tap.arrow.group.classList.toggle("gone", n >= 7 && tap.active);
          tap.arrow.group.classList.toggle("faint", n >= 7 && !tap.active);
        }
      },
    },
  ];
};
