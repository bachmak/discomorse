import pytest
from morse_element_fixtures import character, word, words
from stream_fixtures import stream

from morse_decoder.pipeline.dto import (
    InterCharGap,
    IntraCharGap,
    MorseElement,
    WordGap,
)
from morse_decoder.pipeline.stages.interpreter.dto import (
    CharacterCode,
    MorseSymbol,
    WordBreak,
)
from morse_decoder.pipeline.stages.interpreter.impl.events import _EVENTS, event_of
from morse_decoder.pipeline.stages.interpreter.impl.morse_normalizer import (
    MorseNormalizer,
)


async def _normalize(
    elements: list[MorseElement], *, normalizer: MorseNormalizer | None = None
) -> list[MorseSymbol]:
    """Feed ``elements`` to one normalizer the way the pipeline would."""
    stage = normalizer or MorseNormalizer()
    return [symbol async for symbol in stage.process(stream(*elements))]


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], [], id="empty"),
        pytest.param(
            [WordGap(), InterCharGap(), IntraCharGap()],
            [],
            id="gaps-alone-say-nothing",
        ),
        pytest.param(
            character(".-"),
            [CharacterCode(".-")],
            id="one-character-closed-by-the-stream-ending",
        ),
        pytest.param(
            word(".-", "-..."),
            [CharacterCode(".-"), CharacterCode("-...")],
            id="one-word",
        ),
        pytest.param(
            words((".", "-"), ("...",)),
            [CharacterCode("."), CharacterCode("-"), WordBreak(), CharacterCode("...")],
            id="two-words",
        ),
        pytest.param(
            [WordGap(), *character(".-")],
            [CharacterCode(".-")],
            id="opening-silence-dropped",
        ),
        pytest.param(
            [*character(".-"), WordGap()],
            [CharacterCode(".-")],
            id="closing-silence-dropped",
        ),
        pytest.param(
            [*character(".-"), WordGap(), IntraCharGap(), WordGap(), *character("-")],
            [CharacterCode(".-"), WordBreak(), CharacterCode("-")],
            id="one-break-however-many-gaps",
        ),
        pytest.param(
            words(("....", ".."), ("--", "-.--")),
            [
                CharacterCode("...."),
                CharacterCode(".."),
                WordBreak(),
                CharacterCode("--"),
                CharacterCode("-.--"),
            ],
            id="hi-my",
        ),
    ],
)
async def test_process_gathers_elements_into_character_codes(
    elements: list[MorseElement], want: list[MorseSymbol]
) -> None:
    assert await _normalize(elements) == want


async def test_process_carries_no_character_across_two_streams() -> None:
    """The decoder never closes the last character, so the stream ending has to."""
    normalizer = MorseNormalizer()

    first = await _normalize(character("."), normalizer=normalizer)
    second = await _normalize(character("-"), normalizer=normalizer)

    assert (first, second) == ([CharacterCode(".")], [CharacterCode("-")])


def _element_kinds(root: type[MorseElement]) -> list[type[MorseElement]]:
    """Every kind the decoder can emit: the leaves of the element hierarchy."""
    children = root.__subclasses__()
    return [kind for child in children for kind in _element_kinds(child)] or [root]


@pytest.mark.parametrize("kind", _element_kinds(MorseElement))
def test_every_element_kind_moves_the_machine(kind: type[MorseElement]) -> None:
    assert event_of(kind()) is _EVENTS[kind]
