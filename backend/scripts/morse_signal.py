"""Synthesizes keyed morse audio: the smoke test's stand-in for a recording."""

import io
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import soundfile as sf  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.stages.interpreter.itu import encode_char

_DIT_UNITS = {".": 1, "-": 3}
_INTRA_CHAR_UNITS = 1
_INTER_CHAR_UNITS = 3
_WORD_UNITS = 7


class Tone:
    """A pure sine at a fixed frequency, cut to any number of samples."""

    def __init__(self, sample_rate: int, freq_hz: float, amplitude: float) -> None:
        self._sample_rate = sample_rate
        self._freq_hz = freq_hz
        self._amplitude = amplitude

    def wave(self, samples: int) -> npt.NDArray[PCM16.IntType]:
        t = np.arange(samples) / self._sample_rate
        wave = self._amplitude * np.sin(2 * np.pi * self._freq_hz * t)
        return (wave * PCM16.INT_PEAK).astype(PCM16.IntType)

    def silence(self, samples: int) -> npt.NDArray[PCM16.IntType]:
        return np.zeros(samples, dtype=PCM16.IntType)


@dataclass(frozen=True)
class Segment(ABC):
    """One stretch of the keyed line, measured in dit units."""

    units: int

    @abstractmethod
    def render(self, tone: Tone, samples: int) -> npt.NDArray[PCM16.IntType]:
        """This stretch as PCM, `samples` long."""
        ...


class Mark(Segment):
    """Key down: the tone sounds."""

    def render(self, tone: Tone, samples: int) -> npt.NDArray[PCM16.IntType]:
        return tone.wave(samples)


class Gap(Segment):
    """Key up: nothing sounds."""

    def render(self, tone: Tone, samples: int) -> npt.NDArray[PCM16.IntType]:
        return tone.silence(samples)


class MorseKeyer:
    """Expands text into the segments a straight key would produce."""

    def key(self, message: str) -> Iterator[Segment]:
        for index, word in enumerate(message.split()):
            if index:
                yield Gap(_WORD_UNITS)
            yield from self._key_word(word)

    def _key_word(self, word: str) -> Iterator[Segment]:
        for index, char in enumerate(word):
            if index:
                yield Gap(_INTER_CHAR_UNITS)
            yield from self._key_char(char)

    def _key_char(self, char: str) -> Iterator[Segment]:
        for index, symbol in enumerate(encode_char(char)):
            if index:
                yield Gap(_INTRA_CHAR_UNITS)
            yield Mark(_DIT_UNITS[symbol])


class MorseSignal:
    """Renders a message as WAV bytes at a given speed and pitch."""

    def __init__(
        self,
        sample_rate: int,
        freq_hz: float = 700.0,
        dit_seconds: float = 0.06,
        amplitude: float = 0.5,
    ) -> None:
        self._sample_rate = sample_rate
        self._dit_samples = int(sample_rate * dit_seconds)
        self._tone = Tone(sample_rate, freq_hz, amplitude)
        self._keyer = MorseKeyer()

    def wav(self, message: str) -> bytes:
        return self._encode(self._render(self._keyer.key(message)))

    def _render(self, segments: Iterable[Segment]) -> npt.NDArray[PCM16.IntType]:
        rendered = [
            segment.render(self._tone, segment.units * self._dit_samples)
            for segment in segments
        ]
        return np.concatenate(rendered)

    def _encode(self, samples: npt.NDArray[PCM16.IntType]) -> bytes:
        buffer = io.BytesIO()
        sf.write(
            buffer,
            samples,
            self._sample_rate,
            format="WAV",
            subtype=PCM16.WavSubtype,
        )
        return buffer.getvalue()
