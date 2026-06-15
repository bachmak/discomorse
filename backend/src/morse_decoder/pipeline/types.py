from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MorseElement:
    """One unit the timing decoder reads from the tone stream: a signal or a space."""


class Signal(MorseElement, ABC):
    """A keyed element that contributes to a character's code: a dit or a dah.

    `code_symbol` is its mark in the dot/dash string the letter decoder
    concatenates and looks up. Spaces carry no symbol, so they don't have it.
    """

    @property
    @abstractmethod
    def code_symbol(self) -> str:
        """This element's mark in a character's code: '.' or '-'."""
        ...


class Dit(Signal):
    """A short signal, written '.' in a character's code."""

    @property
    def code_symbol(self) -> str:
        return "."


class Dah(Signal):
    """A long signal, written '-' in a character's code."""

    @property
    def code_symbol(self) -> str:
        return "-"


class Space(MorseElement):
    """A boundary between signals; it carries no code symbol."""


class IntraCharSpace(Space):
    """Gap between the dits and dahs of a single character."""


class InterCharSpace(Space):
    """Gap that ends one character and begins the next."""


class WordSpace(Space):
    """Gap that ends one word and begins the next."""


@dataclass(frozen=True)
class Token(ABC):
    """A decoded morse symbol; the subclass is its kind, `value` its text.

    Each subclass owns the rule for the codes it claims: `claim` builds an
    instance from a decoded code and its ITU character, or returns `None`.
    """

    value: str

    @staticmethod
    @abstractmethod
    def claim(code: str, char: str | None) -> Token | None:
        """Build this kind from a decoded code, or `None` if it doesn't apply."""
        ...


class Unknown(Token):
    """A code with no ITU entry; `value` holds the raw dots and dashes."""

    @staticmethod
    def claim(code: str, char: str | None) -> Unknown | None:
        return Unknown(code) if char is None else None


class Prosign(Token):
    """A procedural signal such as AA, SK, or KN."""

    _MEMBERS = frozenset({"AA", "CT", "SK", "SN", "BT", "KN", "OS"})

    @staticmethod
    def claim(code: str, char: str | None) -> Prosign | None:
        if char is not None and char in Prosign._MEMBERS:
            return Prosign(char)
        return None


class Digit(Token):
    """A numeric digit."""

    _MEMBERS = frozenset("0123456789")

    @staticmethod
    def claim(code: str, char: str | None) -> Digit | None:
        if char is not None and char in Digit._MEMBERS:
            return Digit(char)
        return None


class Letter(Token):
    """Catch-all: any ITU character that no other kind claimed."""

    @staticmethod
    def claim(code: str, char: str | None) -> Letter | None:
        return Letter(char) if char is not None else None
