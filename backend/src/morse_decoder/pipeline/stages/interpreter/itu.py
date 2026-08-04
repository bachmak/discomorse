"""The ITU morse alphabet: the codes and the characters they stand for."""

ITU_TABLE: dict[str, str] = {
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


_CODE_BY_CHAR: dict[str, str] = {char: code for code, char in ITU_TABLE.items()}


def encode_char(char: str) -> str:
    """The ITU code for `char`, or an empty code when it has no entry."""
    return _CODE_BY_CHAR.get(char.upper(), "")


def character_for(code: str) -> str | None:
    """The character `code` spells, or None when the table has no entry."""
    return ITU_TABLE.get(code)
