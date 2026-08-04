"""Turning the tokens a message is made of into the pieces it is written from."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from morse_decoder.pipeline.stages.interpreter.impl.spacing import Marks, Piece, Word
from morse_decoder.pipeline.stages.interpreter.impl.word_segmenter import WordSegmenter
from morse_decoder.pipeline.stages.interpreter.tokens import (
    Digit,
    Letter,
    Prosign,
    Punctuation,
    Token,
    Unknown,
    WordSpace,
)


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
    """A token's part in a message, told apart from the token that plays it."""

    @abstractmethod
    def absorb(
        self, token: Token, assembler: TextAssembler
    ) -> tuple[Piece, ...]: ...


class WordMaterial(TokenRole):
    """Letters and digits: the stuff words are cut out of."""

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_character(token.text())


class Standalone(TokenRole):
    """Punctuation, prosigns and unread codes, none of which sit inside a word."""

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_mark(token.text())


class SpacingHint(TokenRole):
    """A word gap the decoder heard: evidence about where a word begins."""

    def absorb(self, token: Token, assembler: TextAssembler) -> tuple[Piece, ...]:
        return assembler.take_break()


_ROLES: dict[type[Token], TokenRole] = {
    Letter: WordMaterial(),
    Digit: WordMaterial(),
    Punctuation: Standalone(),
    Prosign: Standalone(),
    Unknown: Standalone(),
    WordSpace: SpacingHint(),
}


def role_of(token: Token) -> TokenRole:
    """The part `token` plays; every kind the decoder emits has an entry."""
    try:
        return _ROLES[type(token)]
    except KeyError as exc:
        kind = type(token).__name__
        raise KeyError(f"No wording role for token: {kind}") from exc
