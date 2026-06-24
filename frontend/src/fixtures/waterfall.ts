import type { WaterfallMessage } from "../types/ws";
import { demoSignalLength, demoSignalLevel } from "./oscilloscope";
import { fractNoise } from "./noise";

const BINS = 256;
const CARRIER_BIN = 128;
const DRIFT_BINS = 12;
const CARRIER_WIDTH = 10;
const NOISE_FLOOR = 0.05;

function carrierBin(cursor: number): number {
  return CARRIER_BIN + DRIFT_BINS * Math.sin((2 * Math.PI * cursor) / demoSignalLength);
}

function carrier(bin: number, center: number, level: number): number {
  const offset = bin - center;
  return level * Math.exp(-(offset * offset) / CARRIER_WIDTH);
}

function binMagnitude(bin: number, center: number, level: number, cursor: number): number {
  const noise = NOISE_FLOOR * fractNoise((bin + cursor) * 78.233);
  return Math.min(1, carrier(bin, center, level) + noise);
}

export function demoWaterfallFrame(cursor: number): WaterfallMessage {
  const center = carrierBin(cursor);
  const level = demoSignalLevel(cursor);
  const data = Array.from({ length: BINS }, (_unused, bin) =>
    binMagnitude(bin, center, level, cursor),
  );
  return { type: "waterfall", data, ts: cursor };
}
