import pytest
from stream_fixtures import stream

from morse_decoder.pipeline.stages.interpreter.dto import (
    CharacterCode,
    MorseSymbol,
    WordBreak,
)
from morse_decoder.pipeline.stages.interpreter.letter_decoder import (
    _ITU_TABLE,
    LetterDecoder,
    encode_char,
)
from morse_decoder.pipeline.stages.interpreter.tokens import (
    Digit,
    Letter,
    Prosign,
    Token,
    Unknown,
    WordSpace,
)


async def _decode(symbols: list[MorseSymbol]) -> list[Token]:
    """Feed ``symbols`` to one decoder the way the interpreter would."""
    return [token async for token in LetterDecoder().process(stream(*symbols))]


@pytest.mark.parametrize(
    "symbols, want",
    [
        pytest.param([], [], id="empty"),
        pytest.param([CharacterCode(".-")], [Letter("A")], id="letter"),
        pytest.param([CharacterCode(".----")], [Digit("1")], id="digit"),
        pytest.param([CharacterCode(".-.-.-")], [Letter(".")], id="punctuation"),
        pytest.param([CharacterCode("...-.-")], [Prosign("SK")], id="prosign"),
        pytest.param(
            [CharacterCode("........")],
            [Unknown("........")],
            id="code-outside-the-table",
        ),
        pytest.param([WordBreak()], [WordSpace()], id="word-break"),
        pytest.param(
            [CharacterCode("...."), CharacterCode(".."), WordBreak()],
            [Letter("H"), Letter("I"), WordSpace()],
            id="several-symbols",
        ),
    ],
)
async def test_process_reads_each_symbol_as_its_token(
    symbols: list[MorseSymbol], want: list[Token]
) -> None:
    assert await _decode(symbols) == want


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


@pytest.mark.parametrize("code, char", sorted(_ITU_TABLE.items()))
async def test_every_table_code_decodes_to_its_character(code: str, char: str) -> None:
    """No entry falls through to `Unknown`, and each reads back as itself."""
    (token,) = await _decode([CharacterCode(code)])

    assert not isinstance(token, Unknown)
    assert token.text().strip("<>") == char


@pytest.mark.parametrize("code, char", sorted(_ITU_TABLE.items()))
def test_prosigns_are_the_entries_spelled_with_several_letters(
    code: str, char: str
) -> None:
    """The table decides which codes are prosigns; nothing lists them twice."""
    assert isinstance(LetterDecoder().decode_code(code), Prosign) == (len(char) > 1)


@pytest.mark.parametrize("code, char", sorted(_ITU_TABLE.items()))
def test_encode_char_inverts_the_table(code: str, char: str) -> None:
    assert encode_char(char) == code
