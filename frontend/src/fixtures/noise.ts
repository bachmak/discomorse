export function fractNoise(seed: number): number {
  // deterministic value in [0, 1) — a fract(sin) hash keeps the demo reproducible
  const value = Math.sin(seed) * 43758.5453;
  return value - Math.floor(value);
}
