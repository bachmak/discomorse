from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Token(ABC):
    @abstractmethod
    def text(self) -> str: ...


@dataclass(frozen=True)
class Plain(Token, ABC):
    value: str

    def text(self) -> str:
        return self.value


@dataclass(frozen=True)
class Bracketed(Token, ABC):
    """Set apart in angle brackets: carried by the message but not said in it."""

    value: str

    def text(self) -> str:
        return f"<{self.value}>"


class Letter(Plain):
    pass


class Digit(Plain):
    pass


class Prosign(Bracketed):
    pass


class Unknown(Bracketed):
    pass


@dataclass(frozen=True)
class WordSpace(Token):
    def text(self) -> str:
        return " "
