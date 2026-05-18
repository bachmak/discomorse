from morse_decoder.pipeline.types import MorseElement, Token, TokenKind

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
    "-...-": "BT", "-.---.": "KN", "---...": "OS",
}

_DIGIT_CHARS = set("0123456789")
_PROSIGN_CHARS = {"AA", "CT", "SK", "SN", "BT", "KN", "OS"}


def decode_sequence(elements: list[MorseElement]) -> Token:
    code = "".join(
        "." if e == MorseElement.DIT else "-"
        for e in elements
        if e in (MorseElement.DIT, MorseElement.DAH)
    )
    value = _ITU_TABLE.get(code)
    if value is None:
        return Token(kind=TokenKind.UNKNOWN, value=code)
    if value in _PROSIGN_CHARS:
        return Token(kind=TokenKind.PROSIGN, value=value)
    if value in _DIGIT_CHARS:
        return Token(kind=TokenKind.DIGIT, value=value)
    return Token(kind=TokenKind.LETTER, value=value)
