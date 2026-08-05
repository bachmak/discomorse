import type { DecodedLines } from "./decodedLines";
import { TypedText } from "./typedText";

/** Types out all three readings of a decode, each at the pace its own text arrives. */
export class TypedDecoded {
  private readonly morse = new TypedText();
  private readonly symbols = new TypedText();
  private readonly text = new TypedText();

  shownOf(full: DecodedLines): DecodedLines {
    return {
      morse: this.morse.shownOf(full.morse),
      symbols: this.symbols.shownOf(full.symbols),
      text: this.text.shownOf(full.text),
    };
  }
}
