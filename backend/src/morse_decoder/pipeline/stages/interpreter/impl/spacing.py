"""The pieces a message is written out of, and how they join one another."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

# Marks that cling to the word before them, and to the one after too when what
# they hold together is a number: a time, a decimal, a thousands separator.
_GROUPING_MARKS = ".,:"
_TRAILING_MARKS = ";!?)"
_LEADING_MARKS = "("
_TIGHT_MARKS = "-/_@&'"
_QUOTE = '"'

# `=` and `+` share their codes with the prosigns BT and AR, which separate
# what a message is made of rather than joining it. Standing them apart reads
# right either way round, where closing them up runs whole sentences together.
_STANDING_MARKS = "=+"


@dataclass(frozen=True)
class Piece(ABC):
    """One written unit, and what it wants of the space around it."""

    @abstractmethod
    def text(self) -> str: ...

    def binds_left(self, preceding: "Piece") -> bool:
        """Whether it follows straight on from the piece before it."""
        return False

    def binds_right(self, following: "Piece") -> bool:
        """Whether the piece after it follows straight on."""
        return False

    def is_number(self) -> bool:
        return False


@dataclass(frozen=True)
class Written(Piece, ABC):
    value: str

    def text(self) -> str:
        return self.value


class Word(Written):
    """A word, held apart from whatever sits either side of it."""

    def is_number(self) -> bool:
        return self.value.isdigit()


class Trailing(Written):
    """Closing punctuation, which clings to the word before it."""

    def binds_left(self, preceding: Piece) -> bool:
        return True


class Grouping(Trailing):
    """Punctuation that also clings rightwards when it is grouping digits."""

    def binds_right(self, following: Piece) -> bool:
        return following.is_number()


class Leading(Written):
    """Opening punctuation, which clings to the word after it."""

    def binds_right(self, following: Piece) -> bool:
        return True


class Tight(Written):
    """A mark that joins what it sits between, spaced from neither."""

    def binds_left(self, preceding: Piece) -> bool:
        return True

    def binds_right(self, following: Piece) -> bool:
        return True


class Standing(Written):
    """Set apart on its own: prosigns, and codes nobody recognized."""


class MarkStyle(ABC):
    """How a mark is written, told apart from the mark itself."""

    @abstractmethod
    def piece(self, value: str) -> Piece: ...


class Fixed(MarkStyle):
    def __init__(self, kind: type[Written]) -> None:
        self._kind = kind

    def piece(self, value: str) -> Piece:
        return self._kind(value)


class Paired(MarkStyle):
    """A mark that comes in twos: the first opens, the next one closes."""

    def __init__(self) -> None:
        self._open = False

    def piece(self, value: str) -> Piece:
        self._open = not self._open
        return Leading(value) if self._open else Trailing(value)


_STANDING = Fixed(Standing)


class Marks:
    """Which piece each mark makes; a quote remembers whether it is open."""

    def __init__(self) -> None:
        self._styles = self._styled()

    def piece(self, value: str) -> Piece:
        return self._styles.get(value, _STANDING).piece(value)

    def _styled(self) -> dict[str, MarkStyle]:
        styles: dict[str, MarkStyle] = {}
        styles.update({mark: Fixed(Grouping) for mark in _GROUPING_MARKS})
        styles.update({mark: Fixed(Trailing) for mark in _TRAILING_MARKS})
        styles.update({mark: Fixed(Leading) for mark in _LEADING_MARKS})
        styles.update({mark: Fixed(Tight) for mark in _TIGHT_MARKS})
        styles.update({mark: Fixed(Standing) for mark in _STANDING_MARKS})
        styles[_QUOTE] = Paired()
        return styles


class Writer:
    """Lays pieces down in order, deciding where the spaces fall between them."""

    def __init__(self) -> None:
        self._previous: Piece | None = None

    def write(self, piece: Piece) -> str:
        text = f"{self._gap(piece)}{piece.text()}"
        self._previous = piece
        return text

    def _gap(self, piece: Piece) -> str:
        previous = self._previous
        if previous is None:
            return ""
        joined = previous.binds_right(piece) or piece.binds_left(previous)
        return "" if joined else " "
