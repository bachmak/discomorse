PRES.Controls = class Controls {
  constructor(deck) {
    this.bindings = Controls.bindings(deck);
    document.addEventListener("keydown", (event) => {
      if (this.handle(event.key)) event.preventDefault();
    });
  }

  static bindings(deck) {
    const map = new Map();
    const bind = (keys, action) => keys.forEach((key) => map.set(key, action));
    bind(["ArrowRight", "ArrowDown", " ", "PageDown"], () => deck.next());
    bind(["ArrowLeft", "ArrowUp", "PageUp"], () => deck.prev());
    bind(["Home"], () => deck.go(1));
    bind(["End"], () => deck.go(deck.slides.length));
    bind(["f"], Controls.toggleFullscreen);
    return map;
  }

  handle(key) {
    if (PRES.details.handleKey(key)) return true;
    const action = this.bindings.get(key);
    if (action) action();
    return Boolean(action);
  }

  static toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
};
