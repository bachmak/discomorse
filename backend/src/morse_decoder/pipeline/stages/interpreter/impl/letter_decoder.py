from morse_decoder.pipeline.stages.interpreter.dto import MorseSymbol, SymbolDecoder
from morse_decoder.pipeline.stages.interpreter.impl.classifiers import classify
from morse_decoder.pipeline.stages.interpreter.itu import character_for
from morse_decoder.pipeline.stages.interpreter.tokens import Token, WordSpace


class LetterDecoder(SymbolDecoder):
    """Reads a normalized symbol as the character the ITU table gives it.

    Holds nothing: the normalizer hands over whole codes, so a lookup settles
    each one on its own and every symbol yields exactly one token.
    """

    def decode(self, symbol: MorseSymbol) -> Token:
        return symbol.decoded_by(self)

    def decode_code(self, code: str) -> Token:
        return classify(code, character_for(code))

    def decode_break(self) -> Token:
        return WordSpace()
