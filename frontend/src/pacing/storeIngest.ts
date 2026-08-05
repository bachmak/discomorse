import { useStore } from "../store";
import { PacedIngest } from "./pacedIngest";

// One ingest belongs to one session: whatever it still holds dies with it, so
// an abandoned run can never commit its tail into the store of the next one.
export function storeIngest(): PacedIngest {
  return new PacedIngest(useStore.getState());
}
