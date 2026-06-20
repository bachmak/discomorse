import type { OscilloscopeMessage } from "../types/ws";

const MORSE: Record<string, string> = {
  C: "-.-.", Q: "--.-", S: "...", O: "---", D: "-..", E: ".",
};
const MESSAGE = "CQ CQ";
const SAMPLES_PER_UNIT = 14;
const WINDOW_SAMPLES = 600;
const SCROLL_STEP = 4;
const ON_LEVEL = 0.82;
const NOISE_FLOOR = 0.02;

function keyTimeline(message: string): number[] {
  const units: number[] = [];
  const add = (level: number, count: number): void => {
    for (let i = 0; i < count; i++) units.push(level);
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
  return units;
}

const UNITS = keyTimeline(MESSAGE);
const LOOP_SAMPLES = UNITS.length * SAMPLES_PER_UNIT;
const FRAME_COUNT = Math.round(LOOP_SAMPLES / SCROLL_STEP);

function noise(index: number): number {
  // deterministic value in [0, 1) — a fract(sin) hash keeps the demo reproducible
  const value = Math.sin(index * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function envelopeAt(globalIndex: number): number {
  const level = UNITS[Math.floor(globalIndex / SAMPLES_PER_UNIT) % UNITS.length];
  return level + NOISE_FLOOR * noise(globalIndex);
}

function frameAt(frameIndex: number): number[] {
  const offset = (frameIndex * SCROLL_STEP) % LOOP_SAMPLES;
  return Array.from({ length: WINDOW_SAMPLES }, (_unused, i) => envelopeAt(offset + i));
}

export function demoOscilloscopeFrames(): OscilloscopeMessage[] {
  return Array.from({ length: FRAME_COUNT }, (_unused, i) => ({
    type: "oscilloscope",
    data: frameAt(i),
    ts: i,
  }));
}
