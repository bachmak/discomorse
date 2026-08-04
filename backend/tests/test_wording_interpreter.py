import pytest
from morse_element_fixtures import keyed, spelled, word, words
from stream_fixtures import stream

from morse_decoder.config import InterpreterSettings, PipelineSettings
from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.factory import _build_interpreter
from morse_decoder.pipeline.stages.interpreter.wording_interpreter import (
    WordingInterpreter,
)

_PANGRAM = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"


async def _transcribe(elements: list[MorseElement]) -> str:
    interpreter = WordingInterpreter(InterpreterSettings())
    return "".join(
        [
            transcription.text
            async for transcription in interpreter.process(stream(*elements))
        ]
    )


@pytest.mark.parametrize(
    "message",
    [
        pytest.param("HI MY", id="two-words"),
        pytest.param(_PANGRAM, id="pangram"),
        pytest.param("CQ CQ DE W1AW K", id="calling"),
        pytest.param("UR RST IS 599 IN BOSTON", id="report"),
        pytest.param("MISSISSIPPI BOOKKEEPER COMMITTEE RHYTHM", id="awkward-words"),
    ],
)
async def test_process_leaves_well_spaced_message_as_it_found_it(
    message: str,
) -> None:
    """Spacing the decoder got right is spacing the language has no quarrel with."""
    assert await _transcribe(keyed(message)) == message


@pytest.mark.parametrize(
    "message",
    [
        pytest.param("HI MY", id="two-words"),
        pytest.param(_PANGRAM, id="pangram"),
        pytest.param("MISSISSIPPI BOOKKEEPER COMMITTEE RHYTHM", id="awkward-words"),
        pytest.param("I AM A BIG DOG AND HE IS A CAT", id="single-letter-words"),
    ],
)
async def test_process_regroups_a_message_broken_into_single_characters(
    message: str,
) -> None:
    """The stretched-gap failure: every character arrives as a word of its own."""
    assert await _transcribe(spelled(message)) == message


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param(keyed("DOG. AT"), "DOG. AT", id="full-stop-clings-left"),
        pytest.param(keyed("07:45"), "07:45", id="colon-groups-digits"),
        pytest.param(keyed("AT 07:45, OK"), "AT 07:45, OK", id="time-in-a-sentence"),
        pytest.param(keyed('SENT: "SOS, SOS"'), 'SENT: "SOS, SOS"', id="quotes-pair"),
        pytest.param(keyed("SOS-CHECK"), "SOS-CHECK", id="hyphen-joins"),
        pytest.param(keyed("ANTENNA 3!"), "ANTENNA 3!", id="digit-then-mark"),
        pytest.param(word("...-.-"), "<SK>", id="prosign-stands-alone"),
        pytest.param(
            words(("....", ".."), ("........",)),
            "HI <........>",
            id="unread-code-stands-alone",
        ),
    ],
)
async def test_process_writes_the_marks_where_they_belong(
    elements: list[MorseElement], want: str
) -> None:
    assert await _transcribe(elements) == want


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param(spelled("DOG. AT"), "DOG. AT", id="marks-among-split-letters"),
        pytest.param(spelled("AT 07:45"), "AT 07:45", id="time-among-split-letters"),
        pytest.param(
            spelled("SOS-CHECK"), "SOS-CHECK", id="hyphen-among-split-letters"
        ),
    ],
)
async def test_process_regroups_around_the_marks_it_cannot_move(
    elements: list[MorseElement], want: str
) -> None:
    """A mark never sits inside a word, so it settles the letters ahead of it."""
    assert await _transcribe(elements) == want


async def test_process_publishes_a_word_before_the_message_ends() -> None:
    """The reader watches the text grow, so a word goes out once it settles."""
    interpreter = WordingInterpreter(InterpreterSettings())

    published = [text async for text in interpreter.process(stream(*spelled(_PANGRAM)))]

    assert published[:3] == [
        Transcription(text="THE"),
        Transcription(text=" QUICK"),
        Transcription(text=" BROWN"),
    ]


async def test_process_says_nothing_about_an_empty_stream() -> None:
    assert await _transcribe([]) == ""


def test_factory_builds_the_default_interpreter() -> None:
    assert isinstance(_build_interpreter(PipelineSettings()), WordingInterpreter)
