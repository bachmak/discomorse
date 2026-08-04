from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.api.events import (
    CarrierSampleEvent,
    DigitalToneEvent,
    MorseElementEvent,
    NoiseSampleEvent,
    OutboundEvent,
    ToneEvent,
    ToneSpectrumEvent,
    TranscriptionEvent,
)


@dataclass(frozen=True)
class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> OutboundEvent: ...


@dataclass(frozen=True)
class MorseElement(Serializable, ABC):
    def serialize(self) -> OutboundEvent:
        return MorseElementEvent(data=self.notation())

    @abstractmethod
    def notation(self) -> str: ...


@dataclass(frozen=True)
class Mark(MorseElement, ABC):


@dataclass(frozen=True)
class Dit(Mark):
    def notation(self) -> str:
        return "."


@dataclass(frozen=True)
class Dah(Mark):
    def notation(self) -> str:
        return "-"


@dataclass(frozen=True)
class Gap(MorseElement, ABC):


@dataclass(frozen=True)
class IntraCharGap(Gap):
    def notation(self) -> str:
        return ""


@dataclass(frozen=True)
class InterCharGap(Gap):
    def notation(self) -> str:
        return " "


@dataclass(frozen=True)
class WordGap(Gap):
    def notation(self) -> str:
        return " / "


@dataclass(frozen=True)
class PcmChunk:
    ts: datetime.datetime  # first sample
    data: bytes


@dataclass(frozen=True)
class ToneMagnitude:
    frequency: float
    magnitude: float


@dataclass(frozen=True)
class ToneSpectrum(Serializable):
    ts: datetime.datetime
    magnitudes: tuple[ToneMagnitude, ...]

    def serialize(self) -> OutboundEvent:
        return ToneSpectrumEvent(
            data=[float(tone.magnitude) for tone in self.magnitudes],
            ts=self.ts.timestamp(),
        )


@dataclass(frozen=True)
class Tone(Serializable):
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

    def serialize(self) -> OutboundEvent:
        return ToneEvent(
            frequency=self.frequency,
            magnitude=self.magnitude,
            ts=self.ts.timestamp(),
        )


@dataclass(frozen=True)
class CarrierSample(Serializable):
    tone: Tone
    is_locked: bool

    def serialize(self) -> OutboundEvent:
        return CarrierSampleEvent(
            frequency=self.tone.frequency,
            magnitude=self.tone.magnitude,
            is_locked=self.is_locked,
            ts=self.tone.ts.timestamp(),
        )


@dataclass(frozen=True)
class NoiseSample(Serializable):
    noise: float
    ts: datetime.datetime

    def serialize(self) -> OutboundEvent:
        return NoiseSampleEvent(magnitude=self.noise, ts=self.ts.timestamp())


@dataclass(frozen=True)
class CarrierNoiseSample:
    carrier: CarrierSample
    noise: NoiseSample


@dataclass(frozen=True)
class DigitalTone(Serializable):
    ts: datetime.datetime
    on: bool

    def serialize(self) -> OutboundEvent:
        return DigitalToneEvent(on=self.on, ts=self.ts.timestamp())


@dataclass(frozen=True)
class Transcription(Serializable):
    text: str

    def serialize(self) -> OutboundEvent:
        return TranscriptionEvent(data=self.text)
