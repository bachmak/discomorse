"""The whole symbols the normalizer gathers loose elements into."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.pipeline.stages.symbol_decoder.impl.tokens import Token


class CodeReader(ABC):
    """What a symbol is worth, told apart from the symbol that asks for it."""

    @abstractmethod
    def read_code(self, code: str) -> Token: ...

    @abstractmethod
    def read_break(self) -> Token: ...


@dataclass(frozen=True)
class MorseSymbol(ABC):
    @abstractmethod
    def read_by(self, reader: CodeReader) -> Token: ...


@dataclass(frozen=True)
class CharacterCode(MorseSymbol):
    code: str

    def read_by(self, reader: CodeReader) -> Token:
        return reader.read_code(self.code)


@dataclass(frozen=True)
class WordBreak(MorseSymbol):
    def read_by(self, reader: CodeReader) -> Token:
        return reader.read_break()
