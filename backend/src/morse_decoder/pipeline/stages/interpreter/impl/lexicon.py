"""The words a language uses, priced by how often it uses them."""

from __future__ import annotations

import math
from collections.abc import Mapping
from functools import cache
from importlib.resources import files

_PACKAGE = "morse_decoder"
_LEXICONS = "models"
_FILE = "lexicon.txt"

# Beyond this a candidate is no longer worth testing: the corpus's longest
# entries are compounds the segmenter is better off cutting apart anyway, and
# the span it has to hold open before a word settles grows with the limit.
_LONGEST_WORD = 20


class Lexicon:
    """What each known word costs to say, in nats of surprise."""

    def __init__(self, costs: Mapping[str, float]) -> None:
        self._costs = costs
        self._longest = min(max(map(len, costs), default=0), _LONGEST_WORD)

    def cost_of(self, word: str) -> float | None:
        """What `word` costs, or None when the language does not know it."""
        return self._costs.get(word)

    def knows(self, word: str) -> bool:
        return word in self._costs

    @property
    def longest_word(self) -> int:
        return self._longest


class LexiconFile:
    """The `word<TAB>count` list `scripts/build_lexicon.py` ships per language."""

    def __init__(self, language: str) -> None:
        self._language = language

    def read(self) -> Lexicon:
        counts = self._counts()
        total = sum(counts.values())
        return Lexicon({word: -math.log(c / total) for word, c in counts.items()})

    def _counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for line in self._lines():
            word, _, count = line.partition("\t")
            counts[word] = int(count)
        return counts

    def _lines(self) -> list[str]:
        resource = files(_PACKAGE) / _LEXICONS / self._language / _FILE
        return resource.read_text(encoding="utf-8").splitlines()


@cache
def lexicon_for(language: str) -> Lexicon:
    """The language's lexicon, read once however many sessions ask for it."""
    return LexiconFile(language).read()
