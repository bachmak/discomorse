import { NYQUIST_HZ } from "../audioFormat";
import { fractNoise } from "./noise";

const BIN_COUNT = 256;
const CARRIER_HZ = 700;
const CARRIER_BIN = Math.round((CARRIER_HZ / NYQUIST_HZ) * (BIN_COUNT - 1));
const PEAK_WIDTH_BINS = 6;
const NOISE_FLOOR = 0.05;

function carrierMagnitude(bin: number): number {
  const offset = (bin - CARRIER_BIN) / PEAK_WIDTH_BINS;
  return Math.exp(-offset * offset);
}

export function demoSpectrumFrame(seed: number): number[] {
  return Array.from({ length: BIN_COUNT }, (_unused, bin) =>
    Math.min(1, carrierMagnitude(bin) + NOISE_FLOOR * fractNoise((bin + seed) * 12.9898)),
  );
}
