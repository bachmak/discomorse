import pytest
from morse_element_fixtures import character, word, words
from stream_fixtures import stream

from morse_decoder.config import InterpreterSettings, PipelineSettings
from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    InterCharGap,
    IntraCharGap,
    MorseElement,
    Transcription,
    WordGap,
)
from morse_decoder.pipeline.factory import _build_interpreter
from morse_decoder.pipeline.stages.interpreter.lettering_interpreter import (
    LetteringInterpreter,
)

_HI_MY = words(("....", ".."), ("--", "-.--"))


async def _transcribe(elements: list[MorseElement]) -> str:
    interpreter = LetteringInterpreter(InterpreterSettings())
    return "".join(
        [
            transcription.text
            async for transcription in interpreter.process(stream(*elements))
        ]
    )


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], "", id="empty"),
        pytest.param([WordGap()], "", id="silence-alone-says-nothing"),
        pytest.param(character(".-"), "A", id="one-character"),
        pytest.param(_HI_MY, "HI MY", id="hi-my"),
        pytest.param(word("...", "---", "..."), "SOS", id="run-of-letters"),
        pytest.param(
            words(("-.-.", "--.-"), ("-..", "."), (".--", ".----", ".-", ".--")),
            "CQ DE W1AW",
            id="digits-and-letters",
        ),
        pytest.param(word("...-.-"), "<SK>", id="prosign-is-set-apart"),
        pytest.param(
            words(("....", ".."), ("........",)),
            "HI <........>",
            id="unknown-keeps-its-notation",
        ),
    ],
)
async def test_process_publishes_the_message_the_code_spells(
    elements: list[MorseElement], want: str
) -> None:
    assert await _transcribe(elements) == want


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param(word("...-.-"), "<SK>", id="one-character"),
        pytest.param(word("...-", ".-"), "VA", id="two-characters"),
        pytest.param(word("...", "-", ".-"), "STA", id="three-characters"),
        pytest.param(word(".", ".", ".", "-", ".", "-"), "EEETET", id="six-characters"),
    ],
)
async def test_process_lets_the_gaps_decide_the_characters(
    elements: list[MorseElement], want: str
) -> None:
    """The same six marks throughout; only the gaps holding them apart differ."""
    assert await _transcribe(elements) == want


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([WordGap(), *word("...")], "S", id="leading-word-gap"),
        pytest.param([*word("..."), WordGap()], "S", id="trailing-word-gap"),
        pytest.param(
            [*word("."), WordGap(), WordGap(), *word("-")], "E T", id="doubled-word-gap"
        ),
        pytest.param([Dit(), IntraCharGap()], "E", id="stream-ends-on-a-gap"),
        pytest.param(
            [Dit(), IntraCharGap(), Dah()], "A", id="stream-ends-mid-character"
        ),
        pytest.param(
            [*word("."), WordGap(), IntraCharGap(), InterCharGap(), *word("-")],
            "E T",
            id="run-of-mixed-gaps",
        ),
    ],
)
async def test_process_reads_a_ragged_element_stream(
    elements: list[MorseElement], want: str
) -> None:
    """Whatever the decoder leaves ragged, the text it spells is still clean."""
    assert await _transcribe(elements) == want


async def test_process_transcribes_one_character_at_a_time() -> None:
    """The reader watches the text grow, so a character goes out as it closes."""
    interpreter = LetteringInterpreter(InterpreterSettings())

    transcriptions = interpreter.process(stream(*_HI_MY))

    assert [text async for text in transcriptions] == [
        Transcription(text="H"),
        Transcription(text="I"),
        Transcription(text=" "),
        Transcription(text="M"),
        Transcription(text="Y"),
    ]


def test_factory_builds_the_interpreter_by_name() -> None:
    settings = PipelineSettings(interpreter="LetteringInterpreter")

    assert isinstance(_build_interpreter(settings), LetteringInterpreter)
