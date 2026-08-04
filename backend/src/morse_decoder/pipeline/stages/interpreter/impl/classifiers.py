"""Which kind of token a decoded code stands for."""

from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.interpreter.tokens import (
    Digit,
    Letter,
    Prosign,
    Punctuation,
    Token,
    Unknown,
)

_DIGITS = frozenset("0123456789")


class TokenClassifier(ABC):
    @abstractmethod
    def claim(self, code: str, char: str | None) -> Token | None:
        """Build the token this kind owns for the code, or None to defer."""
        ...


class UnknownClassifier(TokenClassifier):
    def claim(self, code: str, char: str | None) -> Token | None:
        return Unknown(code) if char is None else None


class ProsignClassifier(TokenClassifier):
    """A code the table spells with more than one letter is a procedural signal."""

    def claim(self, code: str, char: str | None) -> Token | None:
        return Prosign(char) if char is not None and len(char) > 1 else None


class DigitClassifier(TokenClassifier):
    def claim(self, code: str, char: str | None) -> Token | None:
        return Digit(char) if char is not None and char in _DIGITS else None


class PunctuationClassifier(TokenClassifier):
    """What the table spells with neither a letter nor a digit is a mark."""

    def claim(self, code: str, char: str | None) -> Token | None:
        return Punctuation(char) if char is not None and not char.isalnum() else None


class LetterClassifier(TokenClassifier):
    def claim(self, code: str, char: str | None) -> Token | None:
        return Letter(char) if char is not None else None


# Asked in order; the first kind that claims the code wins. `Unknown` and
# `Letter` bracket the chain, so every code yields exactly one token.
_CLASSIFIERS: tuple[TokenClassifier, ...] = (
    UnknownClassifier(),
    ProsignClassifier(),
    DigitClassifier(),
    PunctuationClassifier(),
    LetterClassifier(),
)


def classify(code: str, char: str | None) -> Token:
    for classifier in _CLASSIFIERS:
        token = classifier.claim(code, char)
        if token is not None:
            return token
    raise AssertionError("Letter is a catch-all; the chain always yields a token")
