from morse_decoder.pipeline.stages.symbol_decoder.impl.classifiers import classify
from morse_decoder.pipeline.stages.symbol_decoder.impl.symbols import (
    CodeReader,
    MorseSymbol,
)
from morse_decoder.pipeline.stages.symbol_decoder.impl.tokens import Token, WordSpace
from morse_decoder.pipeline.stages.symbol_decoder.itu import character_for


class ItuCodeReader(CodeReader):
    """Reads a normalized symbol as the character the ITU table gives it.

    Holds nothing: the normalizer hands over whole codes, so a lookup settles
    each one on its own and every symbol yields exactly one token.
    """

    def read(self, symbol: MorseSymbol) -> Token:
        return symbol.read_by(self)

    def read_code(self, code: str) -> Token:
        return classify(code, character_for(code))

    def read_break(self) -> Token:
        return WordSpace()
