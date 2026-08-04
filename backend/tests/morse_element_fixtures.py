"""Builders for the elements the interpreter tests drive.

A test writes what it means in notation — codes for the characters, groups for
the words — and gets back the alternating run of marks and gaps the timing
stage would have emitted for it, gaps and all.
"""

from collections.abc import Sequence

from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    InterCharGap,
    IntraCharGap,
    MorseElement,
    WordGap,
)
from morse_decoder.pipeline.stages.interpreter.itu import encode_char

_MARKS: dict[str, MorseElement] = {".": Dit(), "-": Dah()}


def character(code: str) -> list[MorseElement]:
    """One character's marks, held apart by intra-character gaps."""
    spaced: list[MorseElement] = [IntraCharGap()] * (len(code) * 2 - 1)
    spaced[::2] = [_MARKS[mark] for mark in code]
    return spaced


def word(*codes: str) -> list[MorseElement]:
    """One word's characters, held apart by inter-character gaps."""
    return _joined([character(code) for code in codes], InterCharGap())


def words(*codes: tuple[str, ...]) -> list[MorseElement]:
    """Several words, held apart by word gaps."""
    return _joined([word(*group) for group in codes], WordGap())


def keyed(message: str) -> list[MorseElement]:
    """The elements a clean fist would send for `message`."""
    return words(*(tuple(encode_char(char) for char in w) for w in message.split()))


def spelled(message: str) -> list[MorseElement]:
    """The same characters, but with a word gap standing between every one.

    What a character gap stretched past the word threshold makes the timing
    stage report: each character arrives looking like a word of its own.
    """
    return words(*((encode_char(char),) for char in message if not char.isspace()))


def _joined(
    groups: Sequence[list[MorseElement]], separator: MorseElement
) -> list[MorseElement]:
    joined: list[MorseElement] = []
    for group in groups:
        if joined:
            joined.append(separator)
        joined.extend(group)
    return joined
