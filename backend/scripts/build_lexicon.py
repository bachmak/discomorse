"""Builds the word list the interpreter segments against.

The source is a unigram frequency list in Norvig's format — one
`word<TAB>count` line per word, most frequent first:

    curl -L -o count_1w.txt https://norvig.com/ngrams/count_1w.txt
    uv run python scripts/build_lexicon.py count_1w.txt

Written to `src/morse_decoder/models/<language>/lexicon.txt`, which ships
inside the package. Adding a language means running this over that language's
frequency list; no code changes.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

_MODELS = Path(__file__).parents[1] / "src" / "morse_decoder" / "models"
_DEFAULT_SIZE = 50_000

# The only single letters English writes as words. Every other letter is far
# more often a fragment of one, and pricing them as words lets the segmenter
# shred a word it should have kept whole.
_SINGLE_LETTER_WORDS = frozenset({"A", "I"})

# Amateur radio's own vocabulary, which no general corpus carries. The weight
# is a multiple of the rarest count kept from the corpus, so these sit among
# the uncommon words rather than competing with "the".
_HAM_VOCABULARY: dict[int, str] = {
    # A distress call must never be read as the everyday words hiding inside
    # it: MAYDAY is no word of prose, and MAY plus DAY are both common enough
    # to outbid it unless it is weighted well clear of them.
    5_000: "MAYDAY SOS PAN SECURITE",
    500: "CQ DE K R N QTH QRZ QSO QSL RST TNX TU ES OM UR HR DX CW WX RIG ANT"
    " HW CPY FER PWR AGN PSE",
    100: "QRM QRN QSB QSY QRP QRT QRV QRX QSK SK AR KN BK RPT NIL FB OP",
    50: "GM GA GE GN GB CUL YL XYL WPM SSB RTTY QRO ABT HI VY GUD NW SRI HPE",
    20: "TKS BTU WID DR GL CUAGN ELBUG RPRT SIGS",
}


@dataclass(frozen=True)
class Entry:
    word: str
    count: int

    def render(self) -> str:
        return f"{self.word}\t{self.count}"


class Source(ABC):
    """Somewhere entries come from, in the order they should be considered."""

    @abstractmethod
    def entries(self) -> Iterator[Entry]: ...


class FrequencyList(Source):
    """A `word<TAB>count` corpus, cut to its most frequent alphabetic words."""

    def __init__(self, path: Path, size: int) -> None:
        self._path = path
        self._size = size

    def entries(self) -> Iterator[Entry]:
        for line in self._lines():
            word, _, count = line.partition("\t")
            if self._is_word(word):
                yield Entry(word.upper(), int(count))

    def _lines(self) -> list[str]:
        text = self._path.read_text(encoding="utf-8")
        return text.splitlines()[: self._size]

    def _is_word(self, word: str) -> bool:
        return word.isalpha() and (
            len(word) > 1 or word.upper() in _SINGLE_LETTER_WORDS
        )


class HamVocabulary(Source):
    """The service's own words, weighted against the corpus's rarest entry."""

    def __init__(self, floor: int) -> None:
        self._floor = floor

    def entries(self) -> Iterator[Entry]:
        for weight, vocabulary in _HAM_VOCABULARY.items():
            for word in vocabulary.split():
                yield Entry(word, self._floor * weight)


class Lexicon:
    """Every word kept, each at the highest count anything claimed for it."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def absorb(self, source: Source) -> None:
        for entry in source.entries():
            self._counts[entry.word] = max(
                self._counts.get(entry.word, 0), entry.count
            )

    @property
    def floor(self) -> int:
        return min(self._counts.values())

    def render(self) -> str:
        entries = sorted(self._counts.items(), key=lambda pair: -pair[1])
        return "\n".join(Entry(word, count).render() for word, count in entries)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frequency_list", type=Path, help="word<TAB>count corpus")
    parser.add_argument("--language", default="en", help="language code to write under")
    parser.add_argument("--size", type=int, default=_DEFAULT_SIZE, help="words to keep")
    return parser.parse_args()


def main() -> None:
    arguments = _parse_arguments()
    lexicon = Lexicon()
    lexicon.absorb(FrequencyList(arguments.frequency_list, arguments.size))
    lexicon.absorb(HamVocabulary(lexicon.floor))

    target = _MODELS / arguments.language / "lexicon.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(lexicon.render(), encoding="utf-8", newline="\n")
    print(target)


if __name__ == "__main__":
    main()
