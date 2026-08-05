"""The deterministic stage: morse elements in, the tokens they spell out."""

import pytest
from morse_element_fixtures import keyed, spelled, word, words
from stream_fixtures import stream
from token_fixtures import keyed_tokens, spelled_tokens

from morse_decoder.config import PipelineSettings, SymbolDecoderSettings
from morse_decoder.pipeline.dto import MorseElement, Token
from morse_decoder.pipeline.factory import _build_symbol_decoder
from morse_decoder.pipeline.stages.symbol_decoder.itu_symbol_decoder import (
    ItuSymbolDecoder,
)


async def _decoded(elements: list[MorseElement]) -> list[Token]:
    decoder = ItuSymbolDecoder(SymbolDecoderSettings())
    return [token async for token in decoder.process(stream(*elements))]


@pytest.mark.parametrize(
    "message",
    [
        pytest.param("HI MY", id="two-words"),
        pytest.param("THE QUICK BROWN FOX", id="several-words"),
        pytest.param("CQ DE W1AW", id="digits-among-letters"),
        pytest.param("DOG. AT 07:45", id="marks-and-digits"),
    ],
)
async def test_process_spells_the_message_the_elements_carry(message: str) -> None:
    assert await _decoded(keyed(message)) == keyed_tokens(message)


@pytest.mark.parametrize(
    "message",
    [
        pytest.param("HI MY", id="two-words"),
        pytest.param("THE QUICK BROWN FOX", id="several-words"),
    ],
)
async def test_process_reports_the_word_gaps_it_was_given(message: str) -> None:
    """The spacing is passed on as heard; judging it is the corrector's business."""
    assert await _decoded(spelled(message)) == spelled_tokens(message)


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], [], id="empty"),
        pytest.param(word("...-.-"), ["<SK>"], id="prosign-is-set-apart"),
        pytest.param(
            word("........"), ["<........>"], id="unread-code-keeps-its-notation"
        ),
        pytest.param(word(".-.-.-"), ["."], id="punctuation"),
        pytest.param(words(("....",), ("..",)), ["H", " ", "I"], id="word-gap"),
    ],
)
async def test_process_renders_each_kind_of_code(
    elements: list[MorseElement], want: list[str]
) -> None:
    assert [token.value for token in await _decoded(elements)] == want


def test_factory_builds_the_default_symbol_decoder() -> None:
    assert isinstance(_build_symbol_decoder(PipelineSettings()), ItuSymbolDecoder)
