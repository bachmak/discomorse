import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Tone:
    frequency: float
    magnitude: float
    ts: datetime.datetime

    @classmethod
    def empty(cls) -> "Tone":
        return cls(frequency=0.0, magnitude=0.0, ts=datetime.datetime.min)


@dataclass(frozen=True)
class CarrierSample:
    """Where the carrier sits at one spectrum's timestamp, and how loud it is.

    ``is_locked`` separates a frequency the source holds on to from one it merely
    read off the loudest bin while still searching for a carrier.
    """

    tone: Tone
    is_locked: bool


@dataclass(frozen=True)
class CarrierReading:
    samples: tuple[CarrierSample, ...]


@dataclass(frozen=True)
class FrequencyWindow:
    min_hz: float
    max_hz: float
