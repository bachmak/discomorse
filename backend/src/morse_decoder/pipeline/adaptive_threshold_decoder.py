from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

from morse_decoder.config import TimingDecoderSettings
from morse_decoder.pipeline.dto import TimingReading, ToneReading, ToneSample
from morse_decoder.pipeline.types import (
    Dah,
    Dit,
    InterCharSpace,
    IntraCharSpace,
    MorseElement,
    WordSpace,
)
from morse_decoder.plugins.base import TimingDecoder

_PARIS_DIT_SECONDS = 1.2
_DAH_DITS = 3.0


@dataclass(frozen=True)
class Run:
    on: bool
    duration: float


@dataclass(frozen=True)
class _OpenRun:
    on: bool
    start: datetime.datetime

    def close(self, end: datetime.datetime) -> Run:
        return Run(self.on, (end - self.start).total_seconds())


class RunExtractor:
    """Turns a sample stream into closed runs, holding the open run across calls."""

    def __init__(self) -> None:
        self._open: _OpenRun | None = None

    def feed(self, samples: tuple[ToneSample, ...]) -> Iterator[Run]:
        for sample in samples:
            closed = self._advance(sample)
            if closed is not None:
                yield closed

    def _advance(self, sample: ToneSample) -> Run | None:
        if self._open is None:
            self._open = _OpenRun(sample.on, sample.ts)
            return None
        if sample.on == self._open.on:
            return None
        closed = self._open.close(sample.ts)
        self._open = _OpenRun(sample.on, sample.ts)
        return closed


class DitEstimator:
    """Running dit-length estimate, EMA-updated from observed marks."""

    def __init__(self, seed: float, alpha: float) -> None:
        self._dit = seed
        self._alpha = alpha

    @property
    def unit(self) -> float:
        return self._dit

    def observe(self, implied_dit: float) -> None:
        self._dit += self._alpha * (implied_dit - self._dit)


@dataclass(frozen=True)
class Classification:
    element: MorseElement
    implied_dit: float | None = None


class ElementClassifier(ABC):
    @abstractmethod
    def claim(self, run: Run, unit: float) -> Classification | None:
        """Build the element this kind owns for the run, or None to defer."""
        ...


class DitClassifier(ElementClassifier):
    def __init__(self, dah_threshold: float) -> None:
        self._dah_threshold = dah_threshold

    def claim(self, run: Run, unit: float) -> Classification | None:
        if run.on and run.duration < self._dah_threshold * unit:
            return Classification(Dit(), run.duration)
        return None


class DahClassifier(ElementClassifier):
    def claim(self, run: Run, unit: float) -> Classification | None:
        if run.on:
            return Classification(Dah(), run.duration / _DAH_DITS)
        return None


class IntraSpaceClassifier(ElementClassifier):
    def __init__(self, inter_threshold: float) -> None:
        self._inter_threshold = inter_threshold

    def claim(self, run: Run, unit: float) -> Classification | None:
        if not run.on and run.duration < self._inter_threshold * unit:
            return Classification(IntraCharSpace())
        return None


class InterSpaceClassifier(ElementClassifier):
    def __init__(self, word_threshold: float) -> None:
        self._word_threshold = word_threshold

    def claim(self, run: Run, unit: float) -> Classification | None:
        if not run.on and run.duration < self._word_threshold * unit:
            return Classification(InterCharSpace())
        return None


class WordSpaceClassifier(ElementClassifier):
    def claim(self, run: Run, unit: float) -> Classification | None:
        if not run.on:
            return Classification(WordSpace())
        return None


def _classifiers(settings: TimingDecoderSettings) -> tuple[ElementClassifier, ...]:
    return (
        DitClassifier(settings.dah_threshold),
        DahClassifier(),
        IntraSpaceClassifier(settings.inter_char_threshold),
        InterSpaceClassifier(settings.word_threshold),
        WordSpaceClassifier(),
    )


class AdaptiveThresholdDecoder(TimingDecoder):
    """Classifies on/off runs into morse elements against an adaptive dit unit."""

    def __init__(self, settings: TimingDecoderSettings) -> None:
        self._runs = RunExtractor()
        self._estimator = DitEstimator(
            seed=_PARIS_DIT_SECONDS / settings.seed_wpm,
            alpha=settings.alpha,
        )
        self._classifiers = _classifiers(settings)

    async def process(self, reading: ToneReading) -> TimingReading:
        elements = [self._classify(run) for run in self._runs.feed(reading.samples)]
        return TimingReading(elements)

    def _classify(self, run: Run) -> MorseElement:
        result = self._claim(run)
        if result.implied_dit is not None:
            self._estimator.observe(result.implied_dit)
        return result.element

    def _claim(self, run: Run) -> Classification:
        unit = self._estimator.unit
        for classifier in self._classifiers:
            claimed = classifier.claim(run, unit)
            if claimed is not None:
                return claimed
        raise AssertionError("catch-all classifiers always claim a run")
