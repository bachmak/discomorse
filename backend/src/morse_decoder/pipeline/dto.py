from __future__ import annotations

import datetime
from dataclasses import dataclass

from morse_decoder.pipeline.types import MorseElement


@dataclass(frozen=True)
class PcmChunk:
    """The tone detector's input: one chunk of raw Int16 PCM audio."""

    data: bytes


@dataclass(frozen=True)
class ToneSample:
    """A tone detector's on/off verdict at one instant within a chunk."""

    ts: datetime.datetime
    on: bool


@dataclass(frozen=True)
class ToneReading:
    """The tone detector's output: per-chunk tone verdict plus spectrum.

    Doubles as the timing decoder's input: the decoder reads `samples`,
    while `magnitudes` ride along for the waterfall / FFT visualizations.
    """

    samples: tuple[ToneSample, ...]
    magnitudes: list[float]


@dataclass(frozen=True)
class TimingReading:
    """The timing decoder's output: the morse elements decoded this instant.

    Doubles as the interpreter's input. A dedicated type so debug or
    diagnostic fields can be added without changing stage signatures.
    """

    elements: list[MorseElement]


@dataclass(frozen=True)
class Transcription:
    """The interpreter's output: corrected, readable text."""

    text: str
