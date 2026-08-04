from morse_decoder.pipeline.dto import Transcription
from morse_decoder.pipeline.stages.interpreter.dto import MorseSymbol


class NotationTranscriber:
    """Reads a normalized symbol back out as morse notation.

    The space leads a symbol rather than trailing it, so the text a reader is
    watching grow never ends in whitespace held open for the next one.
    """

    def __init__(self) -> None:
        self._opened = False

    def render(self, symbol: MorseSymbol) -> Transcription:
        transcription = Transcription(text=self._spaced(symbol.notation()))
        self._opened = True
        return transcription

    def _spaced(self, notation: str) -> str:
        return f" {notation}" if self._opened else notation
