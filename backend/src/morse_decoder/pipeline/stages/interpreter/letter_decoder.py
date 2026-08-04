from morse_decoder.pipeline.dto import Mark, MorseElement
from morse_decoder.pipeline.stages.interpreter.tokens import (
    Digit,
    Letter,
    Prosign,
    Token,
    Unknown,
)

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

# Asked in order; the first kind that claims the code wins. `Unknown` and
# `Letter` bracket the chain, so every code yields exactly one token.
_TOKEN_TYPES: tuple[type[Token], ...] = (Unknown, Prosign, Digit, Letter)


def encode_char(char: str) -> str:
    """The ITU code for `char`, or an empty code when it has no entry."""
    return _CODE_BY_CHAR.get(char.upper(), "")


def _to_code(elements: list[MorseElement]) -> str:
    """Only marks carry code; a gap's notation is spacing, not a symbol."""
    return "".join(e.notation() for e in elements if isinstance(e, Mark))


def decode_sequence(elements: list[MorseElement]) -> Token:
    code = _to_code(elements)
    char = _ITU_TABLE.get(code)
    for token_type in _TOKEN_TYPES:
        token = token_type.claim(code, char)
        if token is not None:
            return token
    raise AssertionError("Letter is a catch-all; the chain always yields a token")
