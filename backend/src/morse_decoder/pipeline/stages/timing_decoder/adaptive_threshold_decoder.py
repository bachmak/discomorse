from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

from morse_decoder.config import TimingDecoderSettings
from morse_decoder.pipeline.dto import (
    Dah,
    DigitalTone,
    Dit,
    InterCharSpace,
    IntraCharSpace,
    MorseElement,
    ToneSample,
    WordSpace,
)
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder

_PARIS_DIT_SECONDS = 1.2
_DAH_DITS = 3.0
_INTER_SPACE_DITS = 3.0
_INTRA_SPACE_DITS = 1.0


@dataclass(frozen=True)
class Span:
    on: bool
    duration: float


@dataclass(frozen=True)
class _SpanAccumulator:
    on: bool
    start: datetime.datetime

    def close(self, end: datetime.datetime) -> Span:
        return Span(self.on, (end - self.start).total_seconds())


class SpanExtractor:
    """Turns a sample stream into closed spans, holding the open span across calls."""

    def __init__(self) -> None:
        self._accumulator: _SpanAccumulator | None = None

    async def feed(self, samples: AsyncIterable[DigitalTone]) -> AsyncIterator[Span]:
        async for sample in samples:
            span = self._advance(sample)
            if span is not None:
                yield span

    def _advance(self, sample: DigitalTone) -> Span | None:
        if self._accumulator is None:
            self._accumulator = _SpanAccumulator(sample.on, sample.ts)
            return None
        if sample.on == self._accumulator.on:
            return None
        span = self._accumulator.close(sample.ts)
        self._accumulator = _SpanAccumulator(sample.on, sample.ts)
        return span


class DitEstimator:
    """Running dit-length estimate, EMA-updated from observed spans."""

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
    def claim(self, span: Span, unit: float) -> Classification | None:
        """Build the element this kind owns for the span, or None to defer."""
        ...


class DitClassifier(ElementClassifier):
    def __init__(self, dah_threshold: float) -> None:
        self._dah_threshold = dah_threshold

    def claim(self, span: Span, unit: float) -> Classification | None:
        if span.on and span.duration < self._dah_threshold * unit:
            return Classification(Dit(), span.duration)
        return None


class DahClassifier(ElementClassifier):
    def claim(self, span: Span, unit: float) -> Classification | None:
        if span.on:
            return Classification(Dah(), span.duration / _DAH_DITS)
        return None


class IntraSpaceClassifier(ElementClassifier):
    def __init__(self, inter_threshold: float) -> None:
        self._inter_threshold = inter_threshold

    def claim(self, span: Span, unit: float) -> Classification | None:
        if not span.on and span.duration < self._inter_threshold * unit:
            return Classification(IntraCharSpace(), span.duration / _INTRA_SPACE_DITS)
        return None


class InterSpaceClassifier(ElementClassifier):
    def __init__(self, word_threshold: float) -> None:
        self._word_threshold = word_threshold

    def claim(self, span: Span, unit: float) -> Classification | None:
        if not span.on and span.duration < self._word_threshold * unit:
            return Classification(InterCharSpace(), span.duration / _INTER_SPACE_DITS)
        return None


class WordSpaceClassifier(ElementClassifier):
    def claim(self, span: Span, unit: float) -> Classification | None:
        if not span.on:
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
    """Classifies on/off spans into morse elements against an adaptive dit unit."""

    def __init__(self, settings: TimingDecoderSettings) -> None:
        self._extractor = SpanExtractor()
        self._estimator = DitEstimator(
            seed=_PARIS_DIT_SECONDS / settings.seed_wpm,
            alpha=settings.alpha,
        )
        self._classifiers = _classifiers(settings)

    async def process(
        self, samples: AsyncIterable[DigitalTone]
    ) -> AsyncIterator[MorseElement]:
        async for span in self._extractor.feed(samples):
            yield self._classify(span)

    def _classify(self, span: Span) -> MorseElement:
        classification = self._claim(span)
        if classification.implied_dit is not None:
            self._estimator.observe(classification.implied_dit)
        return classification.element

    def _claim(self, span: Span) -> Classification:
        unit = self._estimator.unit
        for classifier in self._classifiers:
            classification = classifier.claim(span, unit)
            if classification is not None:
                return classification
        raise AssertionError("catch-all classifiers always claim a span")
