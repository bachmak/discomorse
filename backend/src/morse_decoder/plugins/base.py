from abc import ABC, abstractmethod
from typing import Any


class ToneDetector(ABC):
    @abstractmethod
    async def process(self, pcm: bytes) -> tuple[bool, list[float]]:
        """Return (tone_on, fft_magnitudes)."""
        ...


class TimingDecoder(ABC):
    @abstractmethod
    async def process(self, tone_on: bool, timestamp: float) -> list[Any]:
        """Return list of timing events (Dit, Dah, spaces)."""
        ...


class Interpreter(ABC):
    @abstractmethod
    async def interpret(self, tokens: list[Any]) -> str:
        """Return corrected, readable text."""
        ...
