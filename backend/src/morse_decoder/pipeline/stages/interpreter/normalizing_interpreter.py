from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.interpreter.morse_normalizer import MorseNormalizer
from morse_decoder.pipeline.stages.interpreter.notation_transcriber import (
    NotationTranscriber,
)


class NormalizingInterpreter(Interpreter):
    """Normalization alone: the elements are gathered, then read back as morse.

    The first of the interpreter's stages. Until the ones behind it land, what
    it publishes is the tidied notation rather than the text behind it.
    """

    def __init__(self, settings: InterpreterSettings) -> None:
        self._normalizer = MorseNormalizer()
        self._transcriber = NotationTranscriber()

    def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Transcription]:
        return self._transcriber.process(self._normalizer.process(elements))
