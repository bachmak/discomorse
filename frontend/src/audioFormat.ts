// Browser→backend WebSocket audio is documented at 8 kHz Int16 PCM (architecture wiki);
// the spectrum axis and the demo carrier are positioned against that band.
export const WS_SAMPLE_RATE_HZ = 8000;
export const NYQUIST_HZ = WS_SAMPLE_RATE_HZ / 2;
