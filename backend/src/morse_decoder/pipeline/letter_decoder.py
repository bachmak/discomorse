from morse_decoder.pipeline.types import (
    Digit,
    Letter,
    MorseElement,
    Prosign,
    Signal,
    Token,
    Unknown,
)

_ITU_TABLE: dict[str, str] = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",", "..--..": "?", ".----.": "'",
    "-.-.--": "!", "-..-.": "/", "-.--.": "(", "-.--.-": ")",
    ".-...": "&", "---...": ":", "-.-.-.": ";", "-...-": "=",
    ".-.-.": "+", "-....-": "-", "..--.-": "_", ".-..-.": '"',
    "...-..-": "$", ".--.-.": "@",
    # Prosigns
    ".-.-": "AA", "-.-.-": "CT", "...-.-": "SK", "...-.": "SN",
    "-.---.": "KN",
}

# Asked in order; the first kind that claims the code wins. `Unknown` and
# `Letter` bracket the chain, so every code yields exactly one token.
_TOKEN_TYPES: tuple[type[Token], ...] = (Unknown, Prosign, Digit, Letter)


def _to_code(elements: list[MorseElement]) -> str:
    return "".join(e.code_symbol for e in elements if isinstance(e, Signal))


def decode_sequence(elements: list[MorseElement]) -> Token:
    code = _to_code(elements)
    char = _ITU_TABLE.get(code)
    for token_type in _TOKEN_TYPES:
        token = token_type.claim(code, char)
        if token is not None:
            return token
    raise AssertionError("Letter is a catch-all; the chain always yields a token")
