from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.pipeline.stages.interpreter.tokens import Token


class SymbolDecoder(ABC):
    """What a symbol is worth, told apart from the symbol that asks for it."""

    @abstractmethod
    def decode_code(self, code: str) -> Token: ...

    @abstractmethod
    def decode_break(self) -> Token: ...


@dataclass(frozen=True)
class MorseSymbol(ABC):
    @abstractmethod
    def notation(self) -> str: ...

    @abstractmethod
    def decoded_by(self, decoder: SymbolDecoder) -> Token: ...


@dataclass(frozen=True)
class CharacterCode(MorseSymbol):
    code: str

    def notation(self) -> str:
        return self.code

    def decoded_by(self, decoder: SymbolDecoder) -> Token:
        return decoder.decode_code(self.code)


@dataclass(frozen=True)
class WordBreak(MorseSymbol):
    def notation(self) -> str:
        return "/"

    def decoded_by(self, decoder: SymbolDecoder) -> Token:
        return decoder.decode_break()
