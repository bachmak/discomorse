from morse_decoder.pipeline.stages.interface import OneToOneStage
from morse_decoder.pipeline.stages.interpreter.dto import MorseSymbol, SymbolDecoder
from morse_decoder.pipeline.stages.interpreter.impl.classifiers import classify
from morse_decoder.pipeline.stages.interpreter.tokens import Token, WordSpace

_ITU_TABLE: dict[str, str] = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    ".-.-.-": ".",
    "--..--": ",",
    "..--..": "?",
    ".----.": "'",
    "-.-.--": "!",
    "-..-.": "/",
    "-.--.": "(",
    "-.--.-": ")",
    ".-...": "&",
    "---...": ":",
    "-.-.-.": ";",
    "-...-": "=",
    ".-.-.": "+",
    "-....-": "-",
    "..--.-": "_",
    ".-..-.": '"',
    "...-..-": "$",
    ".--.-.": "@",
    # Prosigns
    ".-.-": "AA",
    "-.-.-": "CT",
    "...-.-": "SK",
    "...-.": "SN",
    "-.---.": "KN",
}

_CODE_BY_CHAR: dict[str, str] = {char: code for code, char in _ITU_TABLE.items()}


def encode_char(char: str) -> str:
    """The ITU code for `char`, or an empty code when it has no entry."""
    return _CODE_BY_CHAR.get(char.upper(), "")


class LetterDecoder(OneToOneStage[MorseSymbol, Token], SymbolDecoder):
    """Reads each normalized symbol as the character the ITU table gives it.

    Holds nothing: the normalizer hands over whole codes, so a lookup settles
    each one on its own and every symbol yields exactly one token.
    """

    def process_single(self, symbol: MorseSymbol) -> Token:
        return symbol.decoded_by(self)

    def decode_code(self, code: str) -> Token:
        return classify(code, _ITU_TABLE.get(code))

    def decode_break(self) -> Token:
        return WordSpace()
