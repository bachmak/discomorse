"""What a candidate word costs, told apart from the segmenter that asks."""

import math
from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.text_corrector.impl.lexicon import Lexicon

# What share of the words a message uses each kind accounts for. A word is
# nearly always one the language knows; the rest are numbers and the odd
# callsign or abbreviation no corpus carries.
#
# A callsign gets no kind of its own. Priced cheaply enough to be worth
# holding together it swallows the letter after it, reading `W1AW K` as
# `W1AWK`; priced dearly enough not to, it costs more than calling it an
# unrecognized word outright. Nothing useful sits between the two.
_KNOWN_SHARE = 0.90
_NUMBER_SHARE = 0.06
_UNKNOWN_SHARE = 0.04

_LOG_LETTERS = math.log(26.0)
_LOG_DIGITS = math.log(10.0)

# A token nobody recognizes is short — a callsign, a report, an abbreviation.
# Anything longer is two words the segmenter failed to cut apart.
_LONGEST_UNKNOWN = 8

# Standing alone is what makes a lone character suspicious. Every single letter
# English really writes as a word is in the lexicon already, and digits are
# keyed in groups, so an unrecognized one of either is priced as the oddity it
# is. Without this the segmenter happily spells every word out letter by
# letter, which is exactly what a stretched character gap makes it see.
_LONE_UNKNOWN_PENALTY: dict[int, float] = {1: 6.0, 2: 3.0}
_LONE_NUMBER_PENALTY: dict[int, float] = {1: 4.0}


def _opening(share: float) -> float:
    return -math.log(share)


class WordCost(ABC):
    """One kind of word, and what it costs when the candidate is of that kind."""

    @abstractmethod
    def claim(self, word: str) -> float | None:
        """What this kind charges for the word, or None to defer."""
        ...


class KnownWord(WordCost):
    """A word the language knows, at the price its own frequency sets."""

    def __init__(self, lexicon: Lexicon) -> None:
        self._lexicon = lexicon

    def claim(self, word: str) -> float | None:
        cost = self._lexicon.cost_of(word)
        return None if cost is None else _opening(_KNOWN_SHARE) + cost


class Number(WordCost):
    """A run of digits: every digit equally likely, lone ones rare."""

    def claim(self, word: str) -> float | None:
        if not word.isdigit():
            return None
        return (
            _opening(_NUMBER_SHARE)
            + _LOG_DIGITS * len(word)
            + _LONE_NUMBER_PENALTY.get(len(word), 0.0)
        )


class UnknownWord(WordCost):
    """Anything left over, priced as letters drawn at random and capped short."""

    def claim(self, word: str) -> float | None:
        if len(word) > _LONGEST_UNKNOWN:
            return math.inf
        return (
            _opening(_UNKNOWN_SHARE)
            + _LOG_LETTERS * len(word)
            + _LONE_UNKNOWN_PENALTY.get(len(word), 0.0)
        )


class WordPrice:
    """Asks each kind in turn; the first to claim the word sets its price."""

    def __init__(self, lexicon: Lexicon) -> None:
        self._kinds: tuple[WordCost, ...] = (
            KnownWord(lexicon),
            Number(),
            UnknownWord(),
        )

    def of(self, word: str) -> float:
        for kind in self._kinds:
            cost = kind.claim(word)
            if cost is not None:
                return cost
        raise AssertionError("UnknownWord is a catch-all; every word is priced")
