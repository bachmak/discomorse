import { useState } from "react";
import { useStore } from "../store";
import { NO_LINES, sameLines, type DecodedLines } from "../text/decodedLines";
import { TypedDecoded } from "../text/typedDecoded";
import { useFrameLoop } from "./useFrameLoop";

/** The decoded lines as far as they have been typed out, one frame at a time. */
export function useTypedDecoded(): DecodedLines {
  const [typed] = useState(() => new TypedDecoded());
  const [shown, setShown] = useState(NO_LINES);

  useFrameLoop(() => {
    const next = typed.shownOf(useStore.getState().decoded);
    setShown((current) => (sameLines(current, next) ? current : next));
  });

  return shown;
}
