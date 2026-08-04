from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import MorseElement
from morse_decoder.pipeline.stages.interface import ManyToManyStage
from morse_decoder.pipeline.stages.interpreter.dto import MorseSymbol
from morse_decoder.pipeline.stages.interpreter.impl.events import event_of
from morse_decoder.pipeline.stages.interpreter.impl.fsm import (
    LeadingSilence,
    NormalizationState,
    StateTransition,
)


class MorseNormalizer(ManyToManyStage[MorseElement, MorseSymbol]):
    """Gathers loose elements into whole character codes, spacing and all.

    Drives the normalizing machine: each element moves it into its next state.
    What comes out is well formed whatever went in — no empty code, no word
    break ahead of the first character or behind the last, and never two of
    them in a row.
    """

    def __init__(self) -> None:
        self._state: NormalizationState = LeadingSilence()

    async def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[MorseSymbol]:
        async for element in elements:
            for symbol in self._advance(element):
                yield symbol
        for symbol in self._close():
            yield symbol

    def _advance(self, element: MorseElement) -> tuple[MorseSymbol, ...]:
        return self._apply(event_of(element).apply_to(self._state))

    def _close(self) -> tuple[MorseSymbol, ...]:
        """A stream that runs dry ends the character it left open, as a gap would."""
        return self._apply(self._state.end_character())

    def _apply(self, transition: StateTransition) -> tuple[MorseSymbol, ...]:
        self._state = transition.state
        return transition.reported_symbols
