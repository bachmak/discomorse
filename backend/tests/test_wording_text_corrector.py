import pytest
from stream_fixtures import stream
from token_fixtures import WORD_GAP, keyed_tokens, spelled_tokens

from morse_decoder.config import TextCorrectorSettings
from morse_decoder.pipeline.dto import CorrectedText, Token
from morse_decoder.pipeline.stages.text_corrector.wording_text_corrector import (
    WordingTextCorrector,
)

_PANGRAM = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"


async def _corrected(tokens: list[Token]) -> str:
    corrector = WordingTextCorrector(TextCorrectorSettings())
    return "".join(
        [corrected.text async for corrected in corrector.process(stream(*tokens))]
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
async def test_process_leaves_well_spaced_message_as_it_found_it(message: str) -> None:
    """Spacing the decoder got right is spacing the language has no quarrel with."""
    assert await _corrected(keyed_tokens(message)) == message


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
    assert await _corrected(spelled_tokens(message)) == message


@pytest.mark.parametrize(
    "tokens, want",
    [
        pytest.param(keyed_tokens("DOG. AT"), "DOG. AT", id="full-stop-clings-left"),
        pytest.param(keyed_tokens("07:45"), "07:45", id="colon-groups-digits"),
        pytest.param(
            keyed_tokens("AT 07:45, OK"), "AT 07:45, OK", id="time-in-a-sentence"
        ),
        pytest.param(
            keyed_tokens('SENT: "SOS, SOS"'), 'SENT: "SOS, SOS"', id="quotes-pair"
        ),
        pytest.param(keyed_tokens("SOS-CHECK"), "SOS-CHECK", id="hyphen-joins"),
        pytest.param(keyed_tokens("ANTENNA 3!"), "ANTENNA 3!", id="digit-then-mark"),
        pytest.param([Token(value="<SK>")], "<SK>", id="prosign-stands-alone"),
        pytest.param(
            [*keyed_tokens("HI"), WORD_GAP, Token(value="<........>")],
            "HI <........>",
            id="unread-code-stands-alone",
        ),
    ],
)
async def test_process_writes_the_marks_where_they_belong(
    tokens: list[Token], want: str
) -> None:
    assert await _corrected(tokens) == want


@pytest.mark.parametrize(
    "tokens, want",
    [
        pytest.param(
            spelled_tokens("DOG. AT"), "DOG. AT", id="marks-among-split-letters"
        ),
        pytest.param(
            spelled_tokens("AT 07:45"), "AT 07:45", id="time-among-split-letters"
        ),
        pytest.param(
            spelled_tokens("SOS-CHECK"), "SOS-CHECK", id="hyphen-among-split-letters"
        ),
    ],
)
async def test_process_regroups_around_the_marks_it_cannot_move(
    tokens: list[Token], want: str
) -> None:
    """A mark never sits inside a word, so it settles the letters ahead of it."""
    assert await _corrected(tokens) == want


async def test_process_publishes_a_word_before_the_message_ends() -> None:
    """The reader watches the text grow, so a word goes out once it settles."""
    corrector = WordingTextCorrector(TextCorrectorSettings())
    tokens = stream(*spelled_tokens(_PANGRAM))

    published = [text async for text in corrector.process(tokens)]

    assert published[:3] == [
        CorrectedText(text="THE"),
        CorrectedText(text=" QUICK"),
        CorrectedText(text=" BROWN"),
    ]


async def test_process_says_nothing_about_an_empty_stream() -> None:
    assert await _corrected([]) == ""
