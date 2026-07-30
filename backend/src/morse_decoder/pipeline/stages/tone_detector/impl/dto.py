import datetime
from dataclasses import dataclass

from morse_decoder.pipeline.dto import ToneMagnitude, ToneSpectrum


@dataclass(frozen=True)
class CarrierSample:
    """Where the carrier sits at one spectrum's timestamp, and how loud it is.

    ``is_locked`` separates a frequency the source holds on to from one it merely
    read off the loudest bin while still searching for a carrier.
    """

    ts: datetime.datetime
    frequency: float
    magnitude: float
    is_locked: bool


@dataclass(frozen=True)
class CarrierReading:
    samples: tuple[CarrierSample, ...]


@dataclass(frozen=True)
class FrequencyWindow:
    min_hz: float
    max_hz: float


@dataclass(frozen=True)
class SpectrumPeak:
    spectrum: ToneSpectrum
    tone: ToneMagnitude


@dataclass(frozen=True)
class CarrierCandidate:
    """A frequency the peak indicates, and how many spectrums in a row it did."""

    frequency: float
    sightings: int

    @classmethod
    def empty(cls) -> "CarrierCandidate":
        return cls(frequency=0.0, sightings=0)
