// Browser→backend WebSocket audio is documented at 8 kHz Int16 PCM (architecture wiki);
// the spectrum axis and the demo carrier are positioned against that band.
export const WS_SAMPLE_RATE_HZ = 8000;
export const NYQUIST_HZ = WS_SAMPLE_RATE_HZ / 2;

// The backend advances the spectrum by hop_length samples per frame and reads the
// key once per frame, so every stream behind the analyzer — spectrums and digital
// tones alike — ticks at this rate, not at the audio rate.
// Mirrors pipeline.spectrum_analyzer_settings.hop_length in the backend config.
const HOP_SAMPLES = 16;
export const HOP_RATE_HZ = WS_SAMPLE_RATE_HZ / HOP_SAMPLES;

// Spectrum frames carry real-FFT bins: the first sits at DC and the last at
// Nyquist, so it takes bins - 1 steps to cross the band.
export function binFrequency(bin: number, bins: number): number {
  return (bin / Math.max(1, bins - 1)) * NYQUIST_HZ;
}
