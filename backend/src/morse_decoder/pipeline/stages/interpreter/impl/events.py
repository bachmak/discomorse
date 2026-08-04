"""What each kind of decoded element means to the normalizing machine."""

from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    InterCharGap,
    IntraCharGap,
    MorseElement,
    WordGap,
)
from morse_decoder.pipeline.stages.interpreter.impl.fsm import (
    NormalizationState,
    StateTransition,
)


class ElementEvent(ABC):
    """An element's meaning, told apart from the element that carried it."""

    @abstractmethod
    def apply_to(self, state: NormalizationState) -> StateTransition: ...


class MarkSeen(ElementEvent):
    def __init__(self, notation: str) -> None:
        self._notation = notation

    def apply_to(self, state: NormalizationState) -> StateTransition:
        return state.take_mark(self._notation)


class CharacterContinued(ElementEvent):
    """An intra-character gap only holds marks apart; it closes nothing."""

    def apply_to(self, state: NormalizationState) -> StateTransition:
        return state.hold()


class CharacterEnded(ElementEvent):
    def apply_to(self, state: NormalizationState) -> StateTransition:
        return state.end_character()


class WordEnded(ElementEvent):
    def apply_to(self, state: NormalizationState) -> StateTransition:
        return state.end_word()


_EVENTS: dict[type[MorseElement], ElementEvent] = {
    Dit: MarkSeen(Dit().notation()),
    Dah: MarkSeen(Dah().notation()),
    IntraCharGap: CharacterContinued(),
    InterCharGap: CharacterEnded(),
    WordGap: WordEnded(),
}


def event_of(element: MorseElement) -> ElementEvent:
    """What `element` means to the machine; every decoded kind has an entry."""
    try:
        return _EVENTS[type(element)]
    except KeyError as exc:
        kind = type(element).__name__
        raise KeyError(f"No normalization event for element: {kind}") from exc
