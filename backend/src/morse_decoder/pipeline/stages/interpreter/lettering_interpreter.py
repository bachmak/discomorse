from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.interpreter.letter_decoder import LetterDecoder
from morse_decoder.pipeline.stages.interpreter.morse_normalizer import MorseNormalizer
from morse_decoder.pipeline.stages.interpreter.token_transcriber import TokenTranscriber


class LetteringInterpreter(Interpreter):
    """Normalization, then the ITU alphabet: the elements are read as characters.

    The second of the interpreter's stages, working on the codes the first one
    cleaned. Until the ones behind it land, what it publishes is the message
    character by character rather than the words behind it.
    """

    def __init__(self, settings: InterpreterSettings) -> None:
        self._normalizer = MorseNormalizer()
        self._decoder = LetterDecoder()
        self._transcriber = TokenTranscriber()

    def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Transcription]:
        return self._transcriber.process(
            self._decoder.process(self._normalizer.process(elements))
        )
