import type { SubscriptionMessage } from "../types/ws";

// The channels the charts and the decoded panel are fed from. Every other
// stream the pipeline can produce - the symbols between the morse elements and
// the corrected text among them - is diagnostic, so no session asks for it.
export const SUBSCRIPTION: SubscriptionMessage = {
  channels: ["spectrums", "debounced_tones", "morse_elements", "corrected_text"],
};
