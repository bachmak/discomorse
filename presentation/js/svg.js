window.PRES = {};

PRES.svg = (() => {
  const NS = "http://www.w3.org/2000/svg";

  function el(tag, attrs = {}, parent = null) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    }
    if (parent) parent.appendChild(node);
    return node;
  }

  function group(parent, cls = "") {
    return el("g", cls ? { class: cls } : {}, parent);
  }

  function circle(parent, cx, cy, r, cls = "stroke") {
    return el("circle", { cx, cy, r, class: cls }, parent);
  }

  function lineD(a, b) {
    return `M ${a.x} ${a.y} L ${b.x} ${b.y}`;
  }

  function trimmed(a, b, cutA, cutB) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy);
    const ux = dx / len;
    const uy = dy / len;
    return lineD(
      { x: a.x + ux * cutA, y: a.y + uy * cutA },
      { x: b.x - ux * cutB, y: b.y - uy * cutB },
    );
  }

  return { el, group, circle, lineD, trimmed };
})();
