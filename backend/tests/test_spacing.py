"""Where the spaces fall between the pieces a message is written from."""

import pytest

from morse_decoder.pipeline.stages.interpreter.impl.spacing import (
    Leading,
    Marks,
    Piece,
    Standing,
    Trailing,
    Word,
    Writer,
)


def _written(*pieces: Piece) -> str:
    writer = Writer()
    return "".join(writer.write(piece) for piece in pieces)


def _marked(*values: str) -> str:
    """Words and marks told apart the way the assembler tells them apart."""
    marks = Marks()
    pieces = [
        Word(value) if value.isalnum() else marks.piece(value) for value in values
    ]
    return _written(*pieces)


@pytest.mark.parametrize(
    "values, want",
    [
        pytest.param(("HI",), "HI", id="one-word"),
        pytest.param(("HI", "MY"), "HI MY", id="words-are-spaced"),
        pytest.param(("DOG", ".", "AT"), "DOG. AT", id="full-stop-clings-left"),
        pytest.param(("SOS", ",", "SOS"), "SOS, SOS", id="comma-clings-left"),
        pytest.param(("SENT", ":", "OK"), "SENT: OK", id="colon-clings-left"),
        pytest.param(("07", ":", "45"), "07:45", id="colon-groups-digits"),
        pytest.param(("1", ",", "000"), "1,000", id="comma-groups-digits"),
        pytest.param(("3", ".", "5"), "3.5", id="full-stop-groups-digits"),
        pytest.param(("SOS", "-", "CHECK"), "SOS-CHECK", id="hyphen-joins-both-sides"),
        pytest.param(("OK", "?", "YES"), "OK? YES", id="question-mark-clings-left"),
        pytest.param(("HI", "(", "OM", ")"), "HI (OM)", id="brackets-face-inwards"),
        pytest.param(
            ("G4XYZ", "+", "G4XYZ"), "G4XYZ + G4XYZ", id="ar-stands-between-calls"
        ),
        pytest.param(("18C", "=", "HW"), "18C = HW", id="bt-separates-what-it-joins"),
    ],
)
def test_write_puts_each_mark_against_the_word_it_belongs_to(
    values: tuple[str, ...], want: str
) -> None:
    assert _marked(*values) == want


@pytest.mark.parametrize(
    "values, want",
    [
        pytest.param(('"', "SOS", '"'), '"SOS"', id="a-pair-on-its-own"),
        pytest.param(
            ("SENT", ":", '"', "SOS", ",", "SOS", '"'),
            'SENT: "SOS, SOS"',
            id="a-pair-inside-a-sentence",
        ),
        pytest.param(
            ('"', "HI", '"', "AND", '"', "MY", '"'),
            '"HI" AND "MY"',
            id="two-pairs-in-turn",
        ),
    ],
)
def test_write_opens_and_closes_quotes_in_turn(
    values: tuple[str, ...], want: str
) -> None:
    """The first quote of a pair leans right, and the one that answers it leans left."""
    assert _marked(*values) == want


@pytest.mark.parametrize(
    "pieces, want",
    [
        pytest.param((Standing("<SK>"),), "<SK>", id="alone"),
        pytest.param(
            (Word("HI"), Standing("<SK>"), Word("OM")),
            "HI <SK> OM",
            id="spaced-on-both-sides",
        ),
    ],
)
def test_write_sets_a_prosign_apart(pieces: tuple[Piece, ...], want: str) -> None:
    assert _written(*pieces) == want


@pytest.mark.parametrize(
    "piece",
    [
        pytest.param(Word("HI"), id="word"),
        pytest.param(Trailing("."), id="trailing-mark"),
        pytest.param(Leading("("), id="leading-mark"),
    ],
)
def test_write_never_opens_the_message_with_a_space(piece: Piece) -> None:
    """Nothing is owed a space until something has been written for it to follow."""
    assert _written(piece) == piece.text()


def test_marks_reads_an_unlisted_mark_as_one_that_stands_alone() -> None:
    assert Marks().piece("<........>") == Standing("<........>")
