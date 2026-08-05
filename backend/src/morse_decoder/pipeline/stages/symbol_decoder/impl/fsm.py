"""The state machine that gathers loose elements into whole character codes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.pipeline.stages.symbol_decoder.impl.symbols import (
    CharacterCode,
    MorseSymbol,
    WordBreak,
)


@dataclass(frozen=True)
class StateTransition:
    state: NormalizationState
    reported_symbols: tuple[MorseSymbol, ...]


class NormalizationState(ABC):
    """One state of the normalizing machine."""

    @abstractmethod
    def take_mark(self, notation: str) -> StateTransition: ...

    @abstractmethod
    def end_character(self) -> StateTransition: ...

    @abstractmethod
    def end_word(self) -> StateTransition: ...

    def hold(self) -> StateTransition:
        """Nothing to close and nothing to report: the machine stands still."""
        return StateTransition(state=self, reported_symbols=())


class WithinCharacter(NormalizationState):
    """Marks piling up; they go out as one code once a gap closes them."""

    def __init__(self, code: str) -> None:
        self._code = code

    def take_mark(self, notation: str) -> StateTransition:
        return StateTransition(WithinCharacter(self._code + notation), ())

    def end_character(self) -> StateTransition:
        return StateTransition(BetweenCharacters(), (CharacterCode(self._code),))

    def end_word(self) -> StateTransition:
        return StateTransition(BetweenWords(), (CharacterCode(self._code),))


class Quiet(NormalizationState, ABC):
    """No marks in hand: a gap closes nothing, and a mark opens a new code."""

    def take_mark(self, notation: str) -> StateTransition:
        return StateTransition(WithinCharacter(notation), ())

    def end_character(self) -> StateTransition:
        return self.hold()

    def end_word(self) -> StateTransition:
        return self.hold()


class LeadingSilence(Quiet):
    """Before the first mark: a gap ends no word yet, so it is dropped whole."""


class BetweenCharacters(Quiet):
    """A code is out and the word goes on; the next gap may still end it."""

    def end_word(self) -> StateTransition:
        return StateTransition(BetweenWords(), ())


class BetweenWords(Quiet):
    """A word break is owed, and paid only once something arrives to follow it."""

    def take_mark(self, notation: str) -> StateTransition:
        return StateTransition(WithinCharacter(notation), (WordBreak(),))
