from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.stages.interpreter.impl.morse_normalizer import (
    MorseNormalizer,
)
from morse_decoder.pipeline.stages.interpreter.impl.notation_transcriber import (
    NotationTranscriber,
)
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter


class NormalizingInterpreter(Interpreter):
    """Normalization alone: the elements are gathered, then read back as morse.

    The first of the interpreter's stages. What it publishes is the tidied
    notation rather than the text behind it.
    """

    def __init__(self, settings: InterpreterSettings) -> None:
        self._normalizer = MorseNormalizer()
        self._transcriber = NotationTranscriber()

    async def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Transcription]:
        async for symbol in self._normalizer.process(elements):
            yield self._transcriber.render(symbol)
