"""The segmenter on its own: characters and heard breaks in, words out."""

import pytest

from morse_decoder.pipeline.stages.interpreter.impl.lattice import BreakPrior
from morse_decoder.pipeline.stages.interpreter.impl.lexicon import lexicon_for
from morse_decoder.pipeline.stages.interpreter.impl.word_costs import WordPrice
from morse_decoder.pipeline.stages.interpreter.impl.word_segmenter import WordSegmenter

_BREAK = " "


def _segmenter(join: float = 5.0, split: float = 5.0) -> WordSegmenter:
    lexicon = lexicon_for("en")
    return WordSegmenter(
        price=WordPrice(lexicon),
        prior=BreakPrior(join, split),
        lexicon=lexicon,
    )


def _words(written: str, join: float = 5.0, split: float = 5.0) -> list[str]:
    """Feeds `written` through character by character, spaces standing for breaks."""
    segmenter = _segmenter(join, split)
    words: list[str] = []
    for character in written:
        if character == _BREAK:
            segmenter.take_break()
        else:
            words.extend(segmenter.take_character(character))
    words.extend(segmenter.settle())
    return words


@pytest.mark.parametrize(
    "written, want",
    [
        pytest.param("", [], id="empty"),
        pytest.param("THE", ["THE"], id="one-word"),
        pytest.param("THE DOG", ["THE", "DOG"], id="spacing-already-right"),
        pytest.param(
            "THE QUICK BROWN FOX",
            ["THE", "QUICK", "BROWN", "FOX"],
            id="several-words",
        ),
        pytest.param("CQ DE W1AW", ["CQ", "DE", "W1AW"], id="callsign-kept-whole"),
        pytest.param("UR RST IS 599", ["UR", "RST", "IS", "599"], id="report"),
        pytest.param("MY QTH IS 12345", ["MY", "QTH", "IS", "12345"], id="number"),
    ],
)
def test_take_character_leaves_good_spacing_alone(
    written: str, want: list[str]
) -> None:
    """What the decoder got right, the language has no reason to overrule."""
    assert _words(written) == want


@pytest.mark.parametrize(
    "written, want",
    [
        pytest.param("T H E", ["THE"], id="one-word-spelled-out"),
        pytest.param(
            "T H E Q U I C K B R O W N F O X",
            ["THE", "QUICK", "BROWN", "FOX"],
            id="every-letter-its-own-word",
        ),
        pytest.param(
            "I A M A B I G D O G",
            ["I", "AM", "A", "BIG", "DOG"],
            id="real-single-letter-words-survive",
        ),
        pytest.param("5 9 9", ["599"], id="digits-regrouped"),
        pytest.param("0 7", ["07"], id="leading-zero-kept"),
    ],
)
def test_take_character_repairs_a_break_between_every_letter(
    written: str, want: list[str]
) -> None:
    """What a stretched character gap looks like: a word gap after each letter."""
    assert _words(written) == want


@pytest.mark.parametrize(
    "written, want",
    [
        pytest.param("THEDOG", ["THE", "DOG"], id="two-words-run-together"),
        pytest.param(
            "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG",
            ["THE", "QUICK", "BROWN", "FOX", "JUMPS", "OVER", "THE", "LAZY", "DOG"],
            id="whole-sentence-run-together",
        ),
        pytest.param(
            "THE QUI CK BRO WN FOX",
            ["THE", "QUICK", "BROWN", "FOX"],
            id="breaks-in-the-wrong-places",
        ),
    ],
)
def test_take_character_repairs_missing_and_misplaced_breaks(
    written: str, want: list[str]
) -> None:
    assert _words(written) == want


@pytest.mark.parametrize(
    "written, want",
    [
        pytest.param("MAYDAY", ["MAYDAY"], id="one-call"),
        pytest.param(
            "MAYDAY MAYDAY MAYDAY",
            ["MAYDAY", "MAYDAY", "MAYDAY"],
            id="called-three-times"
        ),
        pytest.param(
            " ".join("MAYDAYMAYDAY"),
            ["MAYDAY", "MAYDAY"],
            id="spelled-out-letter-by-letter",
        ),
    ],
)
def test_take_character_never_reads_a_distress_call_as_two_words(
    written: str, want: list[str]
) -> None:
    """`MAY` and `DAY` are both commoner than `MAYDAY`, and must still lose to it."""
    assert _words(written) == want


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("MISSISSIPPI", id="doubled-letters"),
        pytest.param("BOOKKEEPER", id="doubled-pairs"),
        pytest.param("COMMITTEE", id="doubled-twice"),
        pytest.param("RHYTHM", id="no-vowels"),
    ],
)
def test_take_character_keeps_an_awkward_word_whole(written: str) -> None:
    """Words that invite a bad cut are still read as the one word they are."""
    assert _words(written) == [written]


def test_settle_gives_up_whatever_is_still_held_back() -> None:
    """A message ending mid-word still publishes the letters it got."""
    segmenter = _segmenter()
    for character in "ZZZQ":
        segmenter.take_character(character)

    assert "".join(segmenter.settle()) == "ZZZQ"


def _lag(written: str) -> int:
    """The most characters that ever piled up behind a word before it went out."""
    segmenter = _segmenter()
    consumed = placed = worst = 0
    for character in written:
        if character == _BREAK:
            segmenter.take_break()
            continue
        consumed += 1
        for word in segmenter.take_character(character):
            placed += len(word)
            worst = max(worst, consumed - placed)
    return worst


def test_take_character_hands_a_word_over_as_soon_as_the_decoder_vouches_for_it() -> (
    None
):
    """Sound spacing should not be made to wait on context it does not need."""
    assert _lag("THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG") <= 3


@pytest.mark.parametrize(
    "written, want",
    [
        pytest.param(
            " ".join("THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG"),
            ["THE", "QUICK", "BROWN", "FOX", "JUMPS", "OVER", "THE", "LAZY", "DOG"],
            id="pangram",
        ),
        pytest.param(
            " ".join("URRSTIS599INBOSTON"),
            ["UR", "RST", "IS", "599", "IN", "BOSTON"],
            id="report",
        ),
        pytest.param(
            " ".join("IGOINTOTHEBARN"),
            ["I", "GO", "IN", "TO", "THE", "BARN"],
            id="short-words",
        ),
    ],
)
def test_take_character_will_not_be_hurried_by_a_break_it_cannot_trust(
    written: str, want: list[str]
) -> None:
    """A break between every letter tells the cuts apart from nothing.

    Committing on one would cut `JUMPS OVER` into `JUMP SO VER`, so a word
    carrying breaks inside it never vouches for the cut that closes it.
    """
    assert _words(written) == want


def test_take_character_releases_a_word_before_the_message_ends() -> None:
    """A reader watches words arrive, rather than waiting for the last one."""
    segmenter = _segmenter()
    released = [
        word
        for character in "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
        for word in _fed(segmenter, character)
    ]

    assert released[:3] == ["THE", "QUICK", "BROWN"]


def _fed(segmenter: WordSegmenter, character: str) -> tuple[str, ...]:
    if character == _BREAK:
        segmenter.take_break()
        return ()
    return segmenter.take_character(character)
