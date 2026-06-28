import type { WaterfallMessage } from "../types/ws";
import { demoSpectrumFrame } from "./spectrum";

export function demoWaterfallFrame(cursor: number): WaterfallMessage {
  return { type: "waterfall", data: demoSpectrumFrame(cursor), ts: cursor };
}
