"""The shipped word list, and what it makes a candidate word cost."""

import math

import pytest

from morse_decoder.pipeline.stages.text_corrector.impl.lexicon import lexicon_for
from morse_decoder.pipeline.stages.text_corrector.impl.word_costs import WordPrice

_LEXICON = lexicon_for("en")
_PRICE = WordPrice(_LEXICON)


@pytest.mark.parametrize(
    "word",
    [
        pytest.param("THE", id="commonest-word"),
        pytest.param("QUICK", id="ordinary-word"),
        pytest.param("MISSISSIPPI", id="awkward-word"),
        pytest.param("A", id="a-is-a-word"),
        pytest.param("I", id="i-is-a-word"),
        pytest.param("CQ", id="ham-vocabulary"),
        pytest.param("QTH", id="q-code"),
        pytest.param("K", id="ham-single-letter"),
    ],
)
def test_cost_of_knows_the_word(word: str) -> None:
    assert _LEXICON.cost_of(word) is not None


@pytest.mark.parametrize(
    "letter",
    [pytest.param(letter, id=letter) for letter in "BCDFGHJLMOPSTUVWXYZ"],
)
def test_cost_of_does_not_take_a_lone_letter_for_a_word(letter: str) -> None:
    """Every single letter English writes as a word is listed; the rest are not.

    Pricing them as words is what lets a stretched character gap spell a
    message out one letter at a time.
    """
    assert _LEXICON.cost_of(letter) is None


@pytest.mark.parametrize(
    "cheaper, dearer",
    [
        pytest.param("THE", "QUICK", id="commoner-word-costs-less"),
        pytest.param("AND", "RHYTHM", id="common-beats-awkward"),
        pytest.param("THE", "ZZZZ", id="known-beats-unknown"),
    ],
)
def test_of_prices_the_likelier_word_lower(cheaper: str, dearer: str) -> None:
    assert _PRICE.of(cheaper) < _PRICE.of(dearer)


@pytest.mark.parametrize(
    "word",
    [
        pytest.param("QUICK", id="ordinary-word"),
        pytest.param("BOOKKEEPER", id="long-word"),
        pytest.param("RHYTHM", id="awkward-word"),
    ],
)
def test_of_prices_a_word_below_its_own_letters(word: str) -> None:
    """Keeping a word whole has to beat spelling it out, or nothing ever groups."""
    spelled = sum(_PRICE.of(letter) for letter in word)

    assert _PRICE.of(word) < spelled


@pytest.mark.parametrize(
    "digits",
    [
        pytest.param("07", id="two-digits"),
        pytest.param("599", id="three-digits"),
        pytest.param("12345", id="five-digits"),
    ],
)
def test_of_prices_a_number_below_its_own_digits(digits: str) -> None:
    """Digits are keyed in groups, so a group has to beat the digits apart."""
    apart = sum(_PRICE.of(digit) for digit in digits)

    assert _PRICE.of(digits) < apart


@pytest.mark.parametrize(
    "word, want_usable",
    [
        pytest.param("W1AW", True, id="callsign"),
        pytest.param("ZZZZZZZZ", True, id="at-the-limit"),
        pytest.param("ZZZZZZZZZ", False, id="past-the-limit"),
    ],
)
def test_of_refuses_an_unrecognized_word_that_runs_too_long(
    word: str, want_usable: bool
) -> None:
    assert math.isfinite(_PRICE.of(word)) == want_usable


def test_longest_word_bounds_how_far_a_candidate_reaches() -> None:
    assert 0 < _LEXICON.longest_word <= 20


def test_lexicon_for_reads_the_file_once() -> None:
    assert lexicon_for("en") is _LEXICON
