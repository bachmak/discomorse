"""Cutting a run of characters into the words it most likely spells."""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from morse_decoder.pipeline.stages.text_corrector.impl.lexicon import Lexicon
from morse_decoder.pipeline.stages.text_corrector.impl.word_costs import WordPrice

# A one-character word has no interior, so "no breaks inside it" is true of it
# whatever the spacing looks like. A cut is only vouched for by a word that
# could have failed the test.
_TELLING_BREAK_LENGTH = 2


@dataclass(frozen=True)
class CharacterRun:
    """Characters still to be cut into words, and where a break was heard.

    A position holds a break when the timing stage put a word gap immediately
    before that character. It is what the decoder believed, not what is true:
    a stretched character gap reports a break between every letter, and a
    hurried fist reports none at all.
    """

    text: str = ""
    breaks: frozenset[int] = field(default_factory=frozenset)

    def __len__(self) -> int:
        return len(self.text)

    def extended(self, character: str, after_break: bool) -> CharacterRun:
        marked = self.breaks | {len(self.text)} if after_break else self.breaks
        return CharacterRun(self.text + character, frozenset(marked))

    def dropped(self, count: int) -> CharacterRun:
        """What is left once the first `count` characters have been given out."""
        kept = {position - count for position in self.breaks if position >= count}
        return CharacterRun(self.text[count:], frozenset(kept))

    def word(self, begin: int, end: int) -> str:
        return self.text[begin:end]

    def breaks_within(self, begin: int, end: int) -> int:
        """Breaks a word spanning `begin`..`end` would have to talk over."""
        return sum(1 for position in self.breaks if begin < position < end)

    def opens_on_break(self, begin: int) -> bool:
        """Whether a word starting at `begin` is one the decoder also heard."""
        return begin == 0 or begin in self.breaks


class BreakPrior:
    """What the decoder's own spacing charges for disagreeing with it.

    Evidence rather than instruction. Talking over a break it reported costs
    something, and so does cutting where it reported none, but either is worth
    paying when the words that come out read better for it.
    """

    def __init__(self, join_penalty: float, split_penalty: float) -> None:
        self._join = join_penalty
        self._split = split_penalty

    def cost(self, run: CharacterRun, begin: int, end: int) -> float:
        return self._joining(run, begin, end) + self._splitting(run, begin)

    def _joining(self, run: CharacterRun, begin: int, end: int) -> float:
        return run.breaks_within(begin, end) * self._join

    def _splitting(self, run: CharacterRun, begin: int) -> float:
        return 0.0 if run.opens_on_break(begin) else self._split


class Lattice:
    """The cheapest way to cut a run, and the cut each prefix arrived by.

    `starts[i]` is where the last word of the best reading of the first `i`
    characters begins. Following it back to zero spells that reading out.
    """

    def __init__(
        self,
        run: CharacterRun,
        price: WordPrice,
        prior: BreakPrior,
        longest_word: int,
    ) -> None:
        self._run = run
        self._price = price
        self._prior = prior
        self._longest = longest_word
        self._best = [0.0] + [math.inf] * len(run)
        self._starts = [0] * (len(run) + 1)
        self._fill()

    @property
    def starts(self) -> Sequence[int]:
        return self._starts

    def words_to(self, end: int) -> tuple[str, ...]:
        """The words the best reading spells out, up to `end`."""
        words: list[str] = []
        while end:
            begin = self._starts[end]
            words.append(self._run.word(begin, end))
            end = begin
        return tuple(reversed(words))

    def _fill(self) -> None:
        for end in range(1, len(self._run) + 1):
            for begin in range(max(0, end - self._longest), end):
                self._relax(begin, end)

    def _relax(self, begin: int, end: int) -> None:
        cost = self._cost(begin, end)
        if cost < self._best[end]:
            self._best[end] = cost
            self._starts[end] = begin

    def _cost(self, begin: int, end: int) -> float:
        if self._best[begin] == math.inf:
            return math.inf
        word = self._run.word(begin, end)
        return (
            self._best[begin]
            + self._price.of(word)
            + self._prior.cost(self._run, begin, end)
        )


class SettledPrefix:
    """How much of a lattice no later character can still change.

    However the run grows, the word covering its far end starts within the
    last `longest_word` positions, and everything before that start is the
    best reading of a prefix, which is already settled. So the readings those
    positions arrived by are the only ones still in play, and whatever they
    all agree on is final.
    """

    def __init__(self, starts: Sequence[int], longest_word: int) -> None:
        self._starts = starts
        self._longest = longest_word

    def end(self) -> int:
        heads = self._live_heads()
        while len(heads) > 1:
            deepest = max(heads)
            heads.remove(deepest)
            heads.add(self._starts[deepest])
        return heads.pop()

    def _live_heads(self) -> set[int]:
        last = len(self._starts) - 1
        return set(range(max(0, last - self._longest + 1), last + 1))


class ConfidentPrefix:
    """How much of a lattice the decoder's own spacing already vouches for.

    Waiting until no later character can move a cut is the safe rule, but on a
    stream whose spacing is sound it holds every word back for the length of
    the longest word in the language. A cut the decoder reported itself, closing
    a word the language knows, is worth taking at once.

    A break only counts when it could have failed to: spacing stretched past
    the word threshold reports one between every letter, where it says nothing
    about where a word ends. So the word it closes must carry none inside it,
    and be long enough to have carried some.
    """

    def __init__(
        self, run: CharacterRun, starts: Sequence[int], lexicon: Lexicon
    ) -> None:
        self._run = run
        self._starts = starts
        self._lexicon = lexicon

    def end(self) -> int:
        for cut in self._cuts():
            if self._vouched_for(cut):
                return cut
        return 0

    def _cuts(self) -> Iterator[int]:
        """Where the best reading starts each word, the furthest along first."""
        position = len(self._run)
        while position:
            position = self._starts[position]
            if position:
                yield position

    def _vouched_for(self, cut: int) -> bool:
        begin = self._starts[cut]
        word = self._run.word(begin, cut)
        return (
            len(word) >= _TELLING_BREAK_LENGTH
            and self._run.opens_on_break(cut)
            and self._run.breaks_within(begin, cut) == 0
            and self._lexicon.knows(word)
        )
