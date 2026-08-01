from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MorseElement:
    """One unit the timing decoder reads from the tone stream: a signal or a space."""


class Signal(MorseElement, ABC):
    """A keyed element that contributes to a character's code: a dit or a dah.

    `code_symbol` is its mark in the dot/dash string the letter decoder
    concatenates and looks up. Spaces carry no symbol, so they don't have it.
    """

    @property
    @abstractmethod
    def code_symbol(self) -> str:
        """This element's mark in a character's code: '.' or '-'."""
        ...


class Dit(Signal):
    """A short signal, written '.' in a character's code."""

    @property
    def code_symbol(self) -> str:
        return "."


class Dah(Signal):
    """A long signal, written '-' in a character's code."""

    @property
    def code_symbol(self) -> str:
        return "-"


class Space(MorseElement):
    """A boundary between signals; it carries no code symbol."""


class IntraCharSpace(Space):
    """Gap between the dits and dahs of a single character."""


class InterCharSpace(Space):
    """Gap that ends one character and begins the next."""


class WordSpace(Space):
    """Gap that ends one word and begins the next."""


@dataclass(frozen=True)
class PcmChunk:
    ts: datetime.datetime  # first sample
    data: bytes


@dataclass(frozen=True)
class ToneMagnitude:
    frequency: float
    magnitude: float


@dataclass(frozen=True)
class ToneSpectrum:
    ts: datetime.datetime
    magnitudes: tuple[ToneMagnitude, ...]


@dataclass(frozen=True)
class Tone:
    frequency: float
    magnitude: float
    ts: datetime.datetime

    @classmethod
    def empty(cls) -> Tone:
        return cls(frequency=0.0, magnitude=0.0, ts=datetime.datetime.min)

    def with_magnitude(self, magnitude: float) -> Tone:
        return Tone(frequency=self.frequency, magnitude=magnitude, ts=self.ts)

    def with_ts(self, ts: datetime.datetime) -> Tone:
        return Tone(frequency=self.frequency, magnitude=self.magnitude, ts=ts)


@dataclass(frozen=True)
class CarrierSample:
    """Where the carrier sits at one spectrum's timestamp, and how loud it is.

    ``is_locked`` separates a frequency the source holds on to from one it merely
    read off the loudest bin while still searching for a carrier.
    """

    tone: Tone
    is_locked: bool


@dataclass(frozen=True)
class NoiseSample:
    noise: float


@dataclass(frozen=True)
class CarrierNoiseSample:
    carrier: CarrierSample
    noise: NoiseSample


@dataclass(frozen=True)
class ToneSample:
    ts: datetime.datetime
    on: bool


@dataclass(frozen=True)
class ToneReading:
    samples: tuple[ToneSample, ...]


@dataclass(frozen=True)
class TimingReading:
    elements: list[MorseElement]


@dataclass(frozen=True)
class Transcription:
    text: str
