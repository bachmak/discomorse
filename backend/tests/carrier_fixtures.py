"""Builders for the spectrums, sources and readings the carrier tests drive.

Timelines stamp their spectrums with whole multiples of a ``timedelta`` step, so
the grid stays exact no matter how small the step is — the tracking rules turn
on comparisons against that grid, and a rounded microsecond would move a lock.
"""

import datetime
from dataclasses import dataclass
from typing import Self

import numpy.typing as npt
from audio_fixtures import EPOCH

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import CarrierSourceSettings, SpectrumAnalyzerSettings
from morse_decoder.pipeline.dto import (
    CarrierSample,
    FrequencyWindow,
    PcmChunk,
    SpectrumReading,
    ToneMagnitude,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.carrier_source.peak_carrier_source import (
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)

SETTINGS = CarrierSourceSettings()
MIN_HZ = SETTINGS.carrier_min_hz
MAX_HZ = SETTINGS.carrier_max_hz
WINDOW = FrequencyWindow(MIN_HZ, MAX_HZ)
MIN_MAGNITUDE = SETTINGS.carrier_lock_magnitude
TOLERANCE_HZ = SETTINGS.carrier_lock_tolerance_hz
LOCK_SECONDS = SETTINGS.carrier_lock_seconds
HOLD_SECONDS = SETTINGS.carrier_hold_seconds

CARRIER_HZ = 700.0
RIVAL_HZ = 1_100.0
LOUD = 0.9
STEP_S = LOCK_SECONDS / 2
KEYED = {CARRIER_HZ: LOUD, RIVAL_HZ: 0.0}
SILENT = {CARRIER_HZ: 0.0, RIVAL_HZ: 0.0}
LOCK_PHASE_SECONDS = LOCK_SECONDS * 2
LOCK_PHASE_SPECTRUMS = round(LOCK_PHASE_SECONDS / STEP_S)

ANALYZER_SETTINGS = SpectrumAnalyzerSettings(
    sample_rate=8_000, n_fft=128, hop_length=16
)
SAMPLE_RATE = ANALYZER_SETTINGS.sample_rate
BIN_WIDTH_HZ = ANALYZER_SETTINGS.sample_rate / ANALYZER_SETTINGS.n_fft
FRAME_SECONDS = ANALYZER_SETTINGS.n_fft / ANALYZER_SETTINGS.sample_rate
HOP_SECONDS = ANALYZER_SETTINGS.hop_length / ANALYZER_SETTINGS.sample_rate


def source(settings: CarrierSourceSettings | None = None) -> PeakCarrierSource:
    return PeakCarrierSource(settings or SETTINGS)


def narrow_source(min_hz: float, max_hz: float) -> PeakCarrierSource:
    """A source that reads a window of its own instead of the default one."""
    return source(CarrierSourceSettings(carrier_min_hz=min_hz, carrier_max_hz=max_hz))


def spectrum_at(bins: dict[float, float], ts: datetime.datetime) -> ToneSpectrum:
    return ToneSpectrum(
        ts=ts,
        magnitudes=tuple(
            ToneMagnitude(frequency=frequency, magnitude=magnitude)
            for frequency, magnitude in bins.items()
        ),
    )


def spectrum(bins: dict[float, float], at_second: float = 0.0) -> ToneSpectrum:
    return spectrum_at(bins, EPOCH + datetime.timedelta(seconds=at_second))


def spectrums_at(
    bins: dict[float, float], seconds: tuple[float, ...]
) -> tuple[ToneSpectrum, ...]:
    """The same bins seen at each of ``seconds`` — for streams off the grid."""
    return tuple(spectrum(bins, at_second=at_second) for at_second in seconds)


class SpectrumTimeline:
    """Spectrums on a fixed grid: one spectrum every ``step_seconds``."""

    def __init__(self, step_seconds: float = STEP_S) -> None:
        self._step = datetime.timedelta(seconds=step_seconds)
        self._bins: list[dict[float, float]] = []

    def add(self, bins: dict[float, float], count: int = 1) -> Self:
        self._bins += [bins] * count
        return self

    def hold(self, bins: dict[float, float], seconds: float) -> Self:
        """Stay on ``bins`` for as many whole steps as fit in ``seconds``."""
        return self.add(bins, self.steps_in(seconds))

    def alternate(
        self, bins: dict[float, float], other: dict[float, float], cycles: int, run: int
    ) -> Self:
        """Swap between two spectrums, ``run`` of each, ``cycles`` times over."""
        for _ in range(cycles):
            self.add(bins, run).add(other, run)
        return self

    def steps_in(self, seconds: float) -> int:
        return round(datetime.timedelta(seconds=seconds) / self._step)

    def build(self) -> tuple[ToneSpectrum, ...]:
        return tuple(
            spectrum_at(bins, EPOCH + index * self._step)
            for index, bins in enumerate(self._bins)
        )


def locking_timeline(step_seconds: float = STEP_S) -> SpectrumTimeline:
    """A timeline that has already keyed the carrier long enough to lock it."""
    return SpectrumTimeline(step_seconds).hold(KEYED, LOCK_PHASE_SECONDS)


def track(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    carrier_source: PeakCarrierSource | None = None,
) -> tuple[CarrierSample, ...]:
    """Feed ``spectrums`` to one source the way the pipeline would."""
    tracked = carrier_source or source()
    return tuple(tracked.track(spectrum) for spectrum in spectrums)


def frequencies(samples: tuple[CarrierSample, ...]) -> tuple[float, ...]:
    return tuple(sample.tone.frequency for sample in samples)


def magnitudes(samples: tuple[CarrierSample, ...]) -> tuple[float, ...]:
    return tuple(sample.tone.magnitude for sample in samples)


def lock_flags(samples: tuple[CarrierSample, ...]) -> tuple[bool, ...]:
    return tuple(sample.is_locked for sample in samples)


def first_locked_index(samples: tuple[CarrierSample, ...]) -> int:
    """Where the lock closes; ``len(samples)`` when it never does."""
    return next(
        (index for index, sample in enumerate(samples) if sample.is_locked),
        len(samples),
    )


def seconds_since_epoch(ts: datetime.datetime) -> float:
    return (ts - EPOCH).total_seconds()


@dataclass(frozen=True)
class Phase:
    """A stretch of a keyed signal, and which frames fall wholly inside it.

    A frame that straddles an edge of the stretch reads both sides of it at
    once, so only the frames the stretch covers whole say anything about it.
    """

    start_s: float
    end_s: float

    def covers(self, ts: datetime.datetime) -> bool:
        centre = seconds_since_epoch(ts)
        return (
            centre - FRAME_SECONDS / 2 >= self.start_s
            and centre + FRAME_SECONDS / 2 <= self.end_s
        )


async def analyze(samples: npt.NDArray[PCM16.IntType]) -> SpectrumReading:
    analyzer = STFTSpectrumAnalyzer(ANALYZER_SETTINGS)
    return await analyzer.process(PcmChunk(ts=EPOCH, data=samples.tobytes()))
