const MORSE: Record<string, string> = {
  C: "-.-.", Q: "--.-", S: "...", O: "---", D: "-..", E: ".",
};
const MESSAGE = "CQ CQ CQ";
const SAMPLES_PER_UNIT = 14;
const ON_LEVEL = 0.82;
const NOISE_FLOOR = 0.02;

function noise(index: number): number {
  // deterministic value in [0, 1) — a fract(sin) hash keeps the demo reproducible
  const value = Math.sin(index * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function keyedSignal(message: string): number[] {
  const samples: number[] = [];
  const add = (level: number, units: number): void => {
    const count = units * SAMPLES_PER_UNIT;
    for (let i = 0; i < count; i++) samples.push(level + NOISE_FLOOR * noise(samples.length));
  };
  add(0, 4);
  for (const char of message) {
    if (char === " ") {
      add(0, 7);
      continue;
    }
    for (const symbol of MORSE[char] ?? "") {
      add(ON_LEVEL, symbol === "-" ? 3 : 1);
      add(0, 1);
    }
    add(0, 2);
  }
  add(0, 7);
  return samples;
}

const DEMO_SIGNAL = keyedSignal(MESSAGE);

export const demoSignalLength = DEMO_SIGNAL.length;

export function demoScopeChunk(cursor: number, size: number): number[] {
  return Array.from(
    { length: size },
    (_unused, i) => DEMO_SIGNAL[(cursor + i) % DEMO_SIGNAL.length],
  );
}
