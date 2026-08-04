from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MorseSymbol(ABC):
    @abstractmethod
    def notation(self) -> str: ...


@dataclass(frozen=True)
class CharacterCode(MorseSymbol):
    code: str

    def notation(self) -> str:
        return self.code


@dataclass(frozen=True)
class WordBreak(MorseSymbol):
    def notation(self) -> str:
        return "/"
