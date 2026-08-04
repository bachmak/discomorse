import pytest

from morse_decoder.pipeline.stages.interpreter.dto import (
    CharacterCode,
    MorseSymbol,
    WordBreak,
)
from morse_decoder.pipeline.stages.interpreter.impl.letter_decoder import LetterDecoder
from morse_decoder.pipeline.stages.interpreter.itu import ITU_TABLE, encode_char
from morse_decoder.pipeline.stages.interpreter.tokens import (
    Digit,
    Letter,
    Prosign,
    Token,
    Unknown,
    WordSpace,
)

_TABLE = sorted(ITU_TABLE.items())


def _decode(symbol: MorseSymbol) -> Token:
    return LetterDecoder().decode(symbol)


@pytest.mark.parametrize(
    "symbol, want",
    [
        pytest.param(CharacterCode(".-"), Letter("A"), id="letter"),
        pytest.param(CharacterCode(".----"), Digit("1"), id="digit"),
        pytest.param(CharacterCode(".-.-.-"), Letter("."), id="punctuation"),
        pytest.param(CharacterCode("...-.-"), Prosign("SK"), id="prosign"),
        pytest.param(
            CharacterCode("........"),
            Unknown("........"),
            id="code-outside-the-table",
        ),
        pytest.param(WordBreak(), WordSpace(), id="word-break"),
    ],
)
def test_decode_reads_the_symbol_as_its_token(symbol: MorseSymbol, want: Token) -> None:
    assert _decode(symbol) == want


@pytest.mark.parametrize(
    "token, want",
    [
        pytest.param(Letter("A"), "A", id="letter-reads-as-itself"),
        pytest.param(Digit("5"), "5", id="digit-reads-as-itself"),
        pytest.param(Prosign("SK"), "<SK>", id="prosign-is-set-apart"),
        pytest.param(Unknown("....-.-"), "<....-.->", id="unknown-keeps-its-notation"),
        pytest.param(WordSpace(), " ", id="word-space-is-a-space"),
    ],
)
def test_text_renders_the_token(token: Token, want: str) -> None:
    assert token.text() == want


@pytest.mark.parametrize("code, char", _TABLE)
def test_every_table_code_decodes_to_its_character(code: str, char: str) -> None:
    """No entry falls through to `Unknown`, and each reads back as itself."""
    token = _decode(CharacterCode(code))

    assert not isinstance(token, Unknown)
    assert token.text().strip("<>") == char


@pytest.mark.parametrize("code, char", _TABLE)
def test_prosigns_are_the_entries_spelled_with_several_letters(
    code: str, char: str
) -> None:
    """The table decides which codes are prosigns; nothing lists them twice."""
    assert isinstance(_decode(CharacterCode(code)), Prosign) == (len(char) > 1)


@pytest.mark.parametrize("code, char", _TABLE)
def test_encode_char_inverts_the_table(code: str, char: str) -> None:
    assert encode_char(char) == code
