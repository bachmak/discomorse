import type { SubscriptionMessage } from "../types/ws";

// The channels the charts and the transcript are fed from. Every other stream
// the pipeline can produce is diagnostic, so no session asks the backend for it.
export const SUBSCRIPTION: SubscriptionMessage = {
  channels: ["spectrums", "debounced_tones", "morse_elements", "transcriptions"],
};
