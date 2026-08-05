import { useEffect, useState } from "react";

export type CopyState = "idle" | "copied" | "failed";

export interface Clipboard {
  state: CopyState;
  copy: () => Promise<void>;
}

interface Outcome {
  state: CopyState;
  attempt: number;
}

const IDLE: Outcome = { state: "idle", attempt: 0 };
const FEEDBACK_MS = 1500;

export function useClipboard(value: string): Clipboard {
  const [outcome, setOutcome] = useState<Outcome>(IDLE);

  useEffect(() => {
    if (outcome.state === "idle") return;
    const timer = window.setTimeout(() => setOutcome(IDLE), FEEDBACK_MS);
    return () => window.clearTimeout(timer);
  }, [outcome]);

  const settle = (state: CopyState) =>
    setOutcome((current) => ({ state, attempt: current.attempt + 1 }));

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      settle("copied");
    } catch {
      settle("failed");
    }
  };

  return { state: outcome.state, copy };
}
