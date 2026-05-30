from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True)
class ToneReading:
    """A tone detector's verdict for one PCM chunk: tone state plus its spectrum."""

    tone_on: bool
    magnitudes: list[float]


class MorseElement(Enum):
    DIT = auto()
    DAH = auto()
    INTRA_CHAR_SPACE = auto()
    INTER_CHAR_SPACE = auto()
    WORD_SPACE = auto()


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
