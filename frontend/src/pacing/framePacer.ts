export interface FrameRate {
  currentMs(): number;
}

function waitFrame(ms: number, signal: AbortSignal): Promise<void> {
  if (signal.aborted) return Promise.resolve();
  return new Promise((resolve) => {
    const viaFrame = ms <= 0;
    function settle(): void {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }
    function onAbort(): void {
      if (viaFrame) cancelAnimationFrame(handle);
      else clearTimeout(handle);
      settle();
    }
    const handle = viaFrame ? requestAnimationFrame(settle) : window.setTimeout(settle, ms);
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

export class FramePacer {
  constructor(private readonly rate: FrameRate) {}

  async *frames(signal: AbortSignal): AsyncGenerator<number> {
    for (let index = 0; !signal.aborted; index++) {
      yield index;
      await waitFrame(this.rate.currentMs(), signal);
    }
  }
}
