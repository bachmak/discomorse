from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.api.messages import (
    CarrierSampleMessage,
    DigitalToneMessage,
    NoiseSampleMessage,
    OutboundMessage,
    TextMessage,
    ToneMessage,
    ToneSpectrumMessage,
)

_WIRE_DECIMALS = 4


@dataclass(frozen=True)
class Serializable(ABC):
    @abstractmethod
    def to_message(self) -> OutboundMessage: ...


@dataclass(frozen=True)
class MorseElement(Serializable, ABC):
    def to_message(self) -> OutboundMessage:
        return TextMessage(data=self.notation())

    @abstractmethod
    def notation(self) -> str: ...


@dataclass(frozen=True)
class Mark(MorseElement, ABC):
    pass


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
    pass


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

    def to_message(self) -> OutboundMessage:
        return ToneSpectrumMessage(
            data=[
                round(float(tone.magnitude), _WIRE_DECIMALS) for tone in self.magnitudes
            ],
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

    def to_message(self) -> OutboundMessage:
        return ToneMessage(
            frequency=self.frequency,
            magnitude=self.magnitude,
            ts=self.ts.timestamp(),
        )


@dataclass(frozen=True)
class CarrierSample(Serializable):
    tone: Tone
    is_locked: bool

    def to_message(self) -> OutboundMessage:
        return CarrierSampleMessage(
            frequency=self.tone.frequency,
            magnitude=self.tone.magnitude,
            is_locked=self.is_locked,
            ts=self.tone.ts.timestamp(),
        )


@dataclass(frozen=True)
class NoiseSample(Serializable):
    noise: float
    ts: datetime.datetime

    def to_message(self) -> OutboundMessage:
        return NoiseSampleMessage(magnitude=self.noise, ts=self.ts.timestamp())


@dataclass(frozen=True)
class CarrierNoiseSample:
    carrier: CarrierSample
    noise: NoiseSample


@dataclass(frozen=True)
class DigitalTone(Serializable):
    ts: datetime.datetime
    on: bool

    def to_message(self) -> OutboundMessage:
        return DigitalToneMessage(on=self.on, ts=self.ts.timestamp())


@dataclass(frozen=True)
class Token(Serializable):
    value: str

    def to_message(self) -> OutboundMessage:
        return TextMessage(data=self.value)


@dataclass(frozen=True)
class CorrectedText(Serializable):
    text: str

    def to_message(self) -> OutboundMessage:
        return TextMessage(data=self.text)
