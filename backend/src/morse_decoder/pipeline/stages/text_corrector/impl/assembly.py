"""Turning the tokens a message is made of into the pieces it is written from."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from morse_decoder.pipeline.dto import Token
from morse_decoder.pipeline.stages.text_corrector.impl.spacing import (
    Marks,
    Piece,
    Word,
)
from morse_decoder.pipeline.stages.text_corrector.impl.word_segmenter import (
    WordSegmenter,
)

_WORD_GAP = " "


class TextAssembler:
    """Feeds the segmenter what words are cut from, and writes back what it gives."""

    def __init__(self, segmenter: WordSegmenter, marks: Marks) -> None:
        self._segmenter = segmenter
        self._marks = marks

    def take_character(self, character: str) -> tuple[Piece, ...]:
        return _worded(self._segmenter.take_character(character))

    def take_break(self) -> tuple[Piece, ...]:
        self._segmenter.take_break()
        return ()

    def take_mark(self, value: str) -> tuple[Piece, ...]:
        """A mark never sits inside a word, so it settles everything before it."""
        return (*_worded(self._segmenter.settle()), self._marks.piece(value))

    def close(self) -> tuple[Piece, ...]:
        """The message has ended; whatever is still held back goes out as it is."""
        return _worded(self._segmenter.settle())


def _worded(words: Iterable[str]) -> tuple[Piece, ...]:
    return tuple(Word(word) for word in words)


class TokenRole(ABC):
    """A token's part in a message, told apart from the token that plays it.

    The decoding stage hands over what a code spells rather than which kind of
    thing it spelled, so each role recognizes its own by what it reads as. The
    three are exclusive: only a word gap is written as a space, and only a
    mark or an unread code is written as something that is not a letter or a
    digit.
    """

    @abstractmethod
    def claim(self, token: Token) -> bool:
        """Whether this is the part `token` plays."""
        ...

    @abstractmethod
    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]: ...


class SpacingHint(TokenRole):
    """A word gap the decoder heard: evidence about where a word begins."""

    def claim(self, token: Token) -> bool:
        return token.value == _WORD_GAP

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_break()


class Standalone(TokenRole):
    """Punctuation, prosigns and unread codes, none of which sit inside a word."""

    def claim(self, token: Token) -> bool:
        return not token.value.isalnum()

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_mark(token.value)


class WordMaterial(TokenRole):
    """Letters and digits: the stuff words are cut out of."""

    def claim(self, token: Token) -> bool:
        return True

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_character(token.value)


# Asked in order; the first part that claims the token wins. `WordMaterial` is
# a catch-all, so every token plays exactly one part.
_ROLES: tuple[TokenRole, ...] = (SpacingHint(), Standalone(), WordMaterial())


def role_of(token: Token) -> TokenRole:
    for role in _ROLES:
        if role.claim(token):
            return role
    raise AssertionError("WordMaterial is a catch-all; every token has a part")
