/** The three readings of one decode: what was keyed, what it spells, what the corrector made of it. */
export interface DecodedLines {
  morse: string;
  symbols: string;
  text: string;
}

export const NO_LINES: DecodedLines = { morse: "", symbols: "", text: "" };

export function sameLines(one: DecodedLines, other: DecodedLines): boolean {
  return one.morse === other.morse && one.symbols === other.symbols && one.text === other.text;
}
