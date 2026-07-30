import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class CarrierSample:
    """Where the carrier sits at one spectrum's timestamp, and how loud it is."""

    ts: datetime.datetime
    frequency: float
    magnitude: float


@dataclass(frozen=True)
class CarrierReading:
    """The carrier samples one spectrum reading yields."""

    samples: tuple[CarrierSample, ...]
