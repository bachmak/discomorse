import { fractNoise } from "./noise";

const MORSE: Record<string, string> = {
  C: "-.-.", Q: "--.-", S: "...", O: "---", D: "-..", E: ".",
};
const MESSAGE = "CQ CQ CQ";
const SAMPLES_PER_UNIT = 30; // one dit-unit at 20 WPM, at the scope trace rate
const ON_LEVEL = 0.82;
const NOISE_FLOOR = 0.02;

function keyedSignal(message: string): number[] {
  const samples: number[] = [];
  const add = (level: number, units: number): void => {
    const count = units * SAMPLES_PER_UNIT;
    for (let i = 0; i < count; i++) {
      samples.push(level + NOISE_FLOOR * fractNoise(samples.length * 12.9898));
    }
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

export function demoSignalLevel(cursor: number): number {
  return DEMO_SIGNAL[cursor % DEMO_SIGNAL.length];
}

export function demoKeyingOn(cursor: number): boolean {
  return demoSignalLevel(cursor) > ON_LEVEL / 2;
}
