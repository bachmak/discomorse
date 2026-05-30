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


class TokenKind(Enum):
    LETTER = auto()
    DIGIT = auto()
    PROSIGN = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
