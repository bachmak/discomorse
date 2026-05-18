from dataclasses import dataclass
from enum import Enum, auto


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


@dataclass(frozen=True)
class WaterfallFrame:
    magnitudes: list[float]
    timestamp: float


@dataclass(frozen=True)
class FFTFrame:
    magnitudes: list[float]
    timestamp: float
