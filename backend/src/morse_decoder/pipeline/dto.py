from __future__ import annotations

import datetime
from dataclasses import dataclass

from morse_decoder.pipeline.types import MorseElement


@dataclass(frozen=True)
class PcmChunk:
    data: bytes


@dataclass(frozen=True)
class ToneSample:
    ts: datetime.datetime
    on: bool


@dataclass(frozen=True)
class ToneReading:
    samples: tuple[ToneSample, ...]
    magnitudes: list[float]


@dataclass(frozen=True)
class TimingReading:
    elements: list[MorseElement]


@dataclass(frozen=True)
class Transcription:
    text: str
