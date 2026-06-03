from abc import ABC, abstractmethod

from morse_decoder.config import (
    InterpreterSettings,
    TimingDecoderSettings,
    ToneDetectorSettings,
)
from morse_decoder.pipeline.types import MorseElement, ToneReading, ToneSample
from morse_decoder.plugins.configurable import Plugin


class ToneDetector(Plugin[ToneDetectorSettings], ABC):
    @abstractmethod
    async def process(self, pcm: bytes) -> ToneReading:
        """Analyze one PCM chunk into a tone reading."""
        ...


class TimingDecoder(Plugin[TimingDecoderSettings], ABC):
    @abstractmethod
    async def process(self, samples: tuple[ToneSample, ...]) -> list[MorseElement]:
        """Return the timing elements (dits, dahs, spaces) decoded at this instant."""
        ...


class Interpreter(Plugin[InterpreterSettings], ABC):
    @abstractmethod
    async def interpret(self, elements: list[MorseElement]) -> str:
        """Render decoded elements into corrected, readable text."""
        ...
