"""Grouping a stream of characters into the words it spells."""

from morse_decoder.pipeline.stages.interpreter.impl.lattice import (
    BreakPrior,
    CharacterRun,
    ConfidentPrefix,
    Lattice,
    SettledPrefix,
)
from morse_decoder.pipeline.stages.interpreter.impl.lexicon import Lexicon
from morse_decoder.pipeline.stages.interpreter.impl.word_costs import WordPrice


class WordSegmenter:
    """Holds characters back only as long as their grouping is still open.

    A word goes out once no character still to come could move the cut in
    front of it, or sooner where the decoder's own spacing already vouches
    for that cut. So a reader watches the text arrive word by word, and waits
    for context only on the streams whose spacing cannot be taken at its word.
    """

    def __init__(
        self, price: WordPrice, prior: BreakPrior, lexicon: Lexicon
    ) -> None:
        self._price = price
        self._prior = prior
        self._lexicon = lexicon
        self._longest = lexicon.longest_word
        self._run = CharacterRun()
        self._heard_break = False

    def take_character(self, character: str) -> tuple[str, ...]:
        self._run = self._run.extended(character, self._heard_break)
        self._heard_break = False
        lattice = self._lattice()
        return self._release(lattice, self._committed(lattice))

    def _committed(self, lattice: Lattice) -> int:
        """The furthest cut either rule will stand behind."""
        return max(
            SettledPrefix(lattice.starts, self._longest).end(),
            ConfidentPrefix(self._run, lattice.starts, self._lexicon).end(),
        )

    def take_break(self) -> None:
        """The decoder heard a word gap; the next character opens a word."""
        self._heard_break = True

    def settle(self) -> tuple[str, ...]:
        """Nothing can join this run any more, so every cut in it is final."""
        self._heard_break = False
        return self._release(self._lattice(), len(self._run))

    def _lattice(self) -> Lattice:
        return Lattice(self._run, self._price, self._prior, self._longest)

    def _release(self, lattice: Lattice, end: int) -> tuple[str, ...]:
        words = lattice.words_to(end)
        self._run = self._run.dropped(end)
        return words
