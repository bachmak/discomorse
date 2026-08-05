PRES.Pips = class Pips {
  constructor(nav, deck) {
    this.dots = deck.slides.map((_, i) => this.add(nav, () => deck.go(i + 1)));
  }

  add(nav, pick) {
    const dot = document.createElement("span");
    dot.className = "pip";
    dot.addEventListener("click", pick);
    nav.appendChild(dot);
    return dot;
  }

  mark(index) {
    this.dots.forEach((dot, i) => dot.classList.toggle("on", i === index));
  }
};
