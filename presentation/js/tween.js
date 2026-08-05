PRES.ease = {
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  inOutQuad: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
};

PRES.Tween = class Tween {
  static run({ ms, ease = PRES.ease.inOutCubic, step, done }) {
    let cancelled = false;
    const t0 = performance.now();

    function frame(now) {
      if (cancelled) return;
      const t = Math.min(1, (now - t0) / ms);
      step(ease(t));
      if (t < 1) requestAnimationFrame(frame);
      else if (done) done();
    }

    requestAnimationFrame(frame);
    return () => {
      cancelled = true;
    };
  }

  static after(ms, fn) {
    return setTimeout(fn, ms);
  }
};
