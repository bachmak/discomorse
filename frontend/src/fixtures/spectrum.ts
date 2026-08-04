import { NYQUIST_HZ } from "../audioFormat";
import type { ToneSpectrumMessage } from "../types/ws";
import { demoSignalLength, demoSignalLevel } from "./keying";
import { fractNoise } from "./noise";

const BIN_COUNT = 256;
const CARRIER_HZ = 700;
const CARRIER_BIN = Math.round((CARRIER_HZ / NYQUIST_HZ) * (BIN_COUNT - 1));
const DRIFT_BINS = 12;
const PEAK_WIDTH_BINS = 6;
const NOISE_FLOOR = 0.05;

function carrierBin(cursor: number): number {
  return CARRIER_BIN + DRIFT_BINS * Math.sin((2 * Math.PI * cursor) / demoSignalLength);
}

function carrierMagnitude(bin: number, center: number, level: number): number {
  const offset = (bin - center) / PEAK_WIDTH_BINS;
  return level * Math.exp(-offset * offset);
}

function binMagnitude(bin: number, center: number, level: number, cursor: number): number {
  const noise = NOISE_FLOOR * fractNoise((bin + cursor) * 12.9898);
  return Math.min(1, carrierMagnitude(bin, center, level) + noise);
}

function demoSpectrumFrame(cursor: number): number[] {
  const center = carrierBin(cursor);
  const level = demoSignalLevel(cursor);
  return Array.from({ length: BIN_COUNT }, (_unused, bin) =>
    binMagnitude(bin, center, level, cursor),
  );
}

export function demoSpectrumMessage(cursor: number): ToneSpectrumMessage {
  return { type: "tone_spectrum", data: demoSpectrumFrame(cursor), ts: cursor };
}
