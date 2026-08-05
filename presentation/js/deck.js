PRES.Deck = class Deck {
  constructor(camera, layers) {
    this.camera = camera;
    this.layers = layers;
    this.current = 0;
    this.slides = [
      { header: "discomorse", cam: { cx: -25, cy: 5, w: 1150, h: 580 } },
      { header: "pipeline", cam: { cx: -1, cy: 0, w: 155, h: 80 } },
      { header: "stage", cam: { cx: -30, cy: 0, w: 13.8, h: 8 } },
      { header: "stages", cam: { cx: 10, cy: 0, w: 395, h: 105 } },
      { header: "streams", cam: { cx: 10, cy: -1, w: 400, h: 120 } },
      { header: "pull", cam: { cx: 10, cy: 3, w: 400, h: 120 } },
      { header: "client", cam: { cx: 52, cy: -8, w: 530, h: 155 } },
      { header: "frontend · backend", cam: { cx: 55, cy: -20, w: 555, h: 215 } },
      { header: "deployment", cam: { cx: 57, cy: 32, w: 640, h: 330 } },
    ];
    this.hud = document.getElementById("hud-title");
    this.flipped = false;
    this.pips = this.buildPips();
  }

  buildPips() {
    const nav = document.getElementById("progress");
    return this.slides.map((_, i) => {
      const pip = document.createElement("span");
      pip.className = "pip";
      pip.addEventListener("click", () => this.go(i + 1));
      nav.appendChild(pip);
      return pip;
    });
  }

  start() {
    this.current = 1;
    this.camera.jumpTo(this.slides[0].cam);
    this.applyState(true);
  }

  go(n) {
    const target = Math.max(1, Math.min(this.slides.length, n));
    if (target === this.current && !PRES.details.isOpen()) return;
    if (PRES.details.isOpen()) PRES.details.close();
    if (target === this.current) return;
    this.current = target;
    this.applyState(false);
    document.getElementById("hint").classList.add("off");
  }

  next() { this.go(this.current + 1); }
  prev() { this.go(this.current - 1); }

  applyState(instant) {
    const slide = this.slides[this.current - 1];
    if (instant) this.camera.jumpTo(slide.cam);
    else this.camera.flyTo(slide.cam);
    this.setHeader(slide.header);

    for (const layer of this.layers) {
      const visible = this.current >= layer.range[0] && this.current <= layer.range[1];
      const wasHidden = layer.el.classList.contains("off");
      layer.el.classList.toggle("off", !visible);
      if (visible && wasHidden && layer.enter) layer.enter();
      if (layer.update) layer.update(this.current);
    }

    const wantFlip = this.current >= 6;
    if (wantFlip !== this.flipped) {
      this.flipped = wantFlip;
      PRES.graph.flipAll(wantFlip);
    }
    this.pips.forEach((pip, i) => pip.classList.toggle("on", i + 1 === this.current));
  }

  setHeader(text) {
    if (this.hud.textContent === text) return;
    this.hud.classList.add("swap");
    setTimeout(() => {
      this.hud.textContent = text;
      this.hud.classList.remove("swap");
    }, 280);
  }

  restore() {
    const slide = this.slides[this.current - 1];
    this.setHeader(slide.header);
    this.camera.flyTo(slide.cam);
  }

  handleKey(event) {
    if (PRES.details.handleKey(event.key)) return true;
    const forward = ["ArrowRight", "ArrowDown", " ", "PageDown"];
    const backward = ["ArrowLeft", "ArrowUp", "PageUp"];
    if (forward.includes(event.key)) this.next();
    else if (backward.includes(event.key)) this.prev();
    else if (event.key === "Home") this.go(1);
    else if (event.key === "End") this.go(this.slides.length);
    else if (event.key === "f") this.toggleFullscreen();
    else return false;
    return true;
  }

  toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
};
