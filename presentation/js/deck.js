PRES.Deck = class Deck {
  constructor(camera, layers) {
    this.camera = camera;
    this.layers = layers;
    this.current = 0;
    /* a scene names what is on screen, so slides may share one */
    this.slides = [
      { scene: "title", header: "discomorse", cam: { cx: -25, cy: 5, w: 1150, h: 580 } },
      { scene: "pipeline", header: "pipeline", cam: { cx: -1, cy: 0, w: 155, h: 80 } },
      { scene: "stages", header: "stages", cam: { cx: 10, cy: 0, w: 395, h: 105 } },
      { scene: "streams", header: "streams", cam: { cx: 10, cy: -1, w: 400, h: 120 } },
      { scene: "interface", header: "interface", cam: { cx: -30, cy: 0, w: 13.8, h: 8 } },
      { scene: "streams", header: "streams", cam: { cx: 10, cy: -1, w: 400, h: 120 } },
      { scene: "pull", header: "pull", cam: { cx: 10, cy: 3, w: 400, h: 120 } },
      { scene: "consumer", header: "consumer", cam: { cx: 52, cy: -8, w: 530, h: 155 } },
      { scene: "system", header: "frontend · backend", cam: { cx: 102, cy: -62, w: 586, h: 230 } },
      { scene: "deployment", header: "deployment", cam: { cx: 102, cy: 55, w: 620, h: 478 } },
    ];
    this.hud = document.getElementById("hud-title");
    this.flipped = false;
    this.pips = new PRES.Pips(document.getElementById("progress"), this);
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

  reached(scene) {
    return this.current > this.slides.findIndex((slide) => slide.scene === scene);
  }

  applyState(instant) {
    const slide = this.slides[this.current - 1];
    const flight = instant ? this.camera.jumpTo(slide.cam) : this.camera.flyTo(slide.cam);
    this.setHeader(slide.header);
    const revealed = this.showLayers(slide.scene);
    this.syncFlip(revealed ? flight * 0.55 : 0);
    this.pips.mark(this.current - 1);
  }

  showLayers(scene) {
    let revealed = false;
    for (const layer of this.layers) {
      const visible = layer.on.includes(scene);
      const wasHidden = layer.el.classList.contains("off");
      layer.el.classList.toggle("off", !visible);
      if (visible && wasHidden) {
        revealed = true;
        if (layer.enter) layer.enter();
      }
      if (layer.update) layer.update(scene);
    }
    return revealed;
  }

  /* arrows that just faded in are worth turning only once the camera lands */
  syncFlip(lead) {
    const wanted = this.reached("pull");
    if (wanted === this.flipped) return;
    this.flipped = wanted;
    PRES.graph.flipAll(wanted, lead);
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
};
