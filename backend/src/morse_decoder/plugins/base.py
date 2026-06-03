from abc import ABC, abstractmethod

from morse_decoder.pipeline.types import MorseElement, ToneReading
from morse_decoder.plugins.configurable import Plugin


class ToneDetector(Plugin, ABC):
    @abstractmethod
    async def process(self, pcm: bytes) -> ToneReading:
        """Analyze one PCM chunk into a tone reading."""
        ...


class TimingDecoder(Plugin, ABC):
    @abstractmethod
    async def process(self, samples: tuple[ToneSample, ...]) -> list[MorseElement]:
        """Return the timing elements (dits, dahs, spaces) decoded at this instant."""
        ...


class Interpreter(Plugin, ABC):
    @abstractmethod
    async def interpret(self, elements: list[MorseElement]) -> str:
        """Render decoded elements into corrected, readable text."""
        ...
