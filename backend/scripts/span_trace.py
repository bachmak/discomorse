"""Measures what the timing decoder sees: span durations against exact keying.

Synthesizes morse from a spec, runs it through a pipeline whose stages are wired
explicitly, and records every span the timing decoder judged. Lets a caller vary
one stage's settings and compare the spans that result.
"""

import datetime
from dataclasses import dataclass

from morse_signal import MorseSignal

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import (
    AudioSettings,
    CarrierSourceSettings,
    InterpreterSettings,
    KeyingDebouncerSettings,
    KeyingDetectorSettings,
    NoiseEstimatorSettings,
    SpectrumAnalyzerSettings,
    SpectrumLimiterSettings,
    TimingDecoderSettings,
)
from morse_decoder.pipeline.dto import MorseElement
from morse_decoder.pipeline.events import DecodedMorse
from morse_decoder.pipeline.pipeline import Pipeline
from morse_decoder.pipeline.stages.carrier_source.peak_carrier_source import (
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.interpreter.dummy_interpreter import DummyInterpreter
from morse_decoder.pipeline.stages.interpreter.letter_decoder import encode_char
from morse_decoder.pipeline.stages.keying_debouncer.timed_keying_debouncer import (
    TimedKeyingDebouncer,
)
from morse_decoder.pipeline.stages.keying_detector.adaptive_keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.noise_estimator.percentile_noise_estimator import (
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)
from morse_decoder.pipeline.stages.spectrum_limiter.static_spectrum_limiter import (
    StaticSpectrumLimiter,
)
from morse_decoder.pipeline.stages.timing_decoder.adaptive_threshold_decoder import (
    AdaptiveThresholdDecoder,
    Span,
)

_PARIS_DIT_SECONDS = 1.2
_EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
_CANONICAL_UNITS = (1, 3, 7)


@dataclass(frozen=True)
class SignalSpec:
    message: str
    freq_hz: float
    wpm: float
    sample_rate: int

    @property
    def dit_seconds(self) -> float:
        return _PARIS_DIT_SECONDS / self.wpm

    def wav(self) -> bytes:
        return MorseSignal(self.sample_rate, self.freq_hz, self.dit_seconds).wav(
            self.message
        )

    def reference(self) -> str:
        return " / ".join(
            " ".join(encode_char(char) for char in word)
            for word in self.message.split()
        )

    def describe(self) -> str:
        return (
            f"message  {self.message!r}\n"
            f"pitch    {self.freq_hz:.0f} Hz\n"
            f"speed    {self.wpm:.0f} wpm (dit = {self.dit_seconds * 1000:.0f} ms)\n"
            f"rate     {self.sample_rate} Hz, mono\n"
            f"noise    none (mathematically exact keying)"
        )


@dataclass(frozen=True)
class SpanRecord:
    """One measured span, what it was classified as, and the unit that judged it."""

    span: Span
    notation: str
    unit: float

    def true_units(self, dit: float) -> int:
        return min(
            _CANONICAL_UNITS, key=lambda units: abs(self.span.duration - units * dit)
        )

    def skew_seconds(self, dit: float) -> float:
        return self.span.duration - self.true_units(dit) * dit

    def kind(self, dit: float) -> str:
        side = "mark" if self.span.on else "gap"
        return f"{side} {self.true_units(dit)}u"


class TracingDecoder(AdaptiveThresholdDecoder):
    """An AdaptiveThresholdDecoder that keeps every span it judged."""

    def __init__(self, settings: TimingDecoderSettings) -> None:
        super().__init__(settings)
        self.records: list[SpanRecord] = []

    def _classify(self, span: Span) -> MorseElement:
        unit = self._estimator.unit
        element = super()._classify(span)
        self.records.append(SpanRecord(span, element.notation, unit))
        return element


@dataclass(frozen=True)
class Case:
    label: str
    debouncer: KeyingDebouncerSettings


@dataclass(frozen=True)
class Outcome:
    morse: str
    records: tuple[SpanRecord, ...]


class Decoding:
    """One pass of a spec through the pipeline under one debouncer setting."""

    def __init__(self, spec: SignalSpec, case: Case) -> None:
        self._spec = spec
        self._case = case
        self._timing = TimingDecoderSettings()
        self._decoder = TracingDecoder(self._timing)

    async def run(self) -> Outcome:
        notations = [
            event.element.notation
            async for event in self._pipeline().run()
            if isinstance(event, DecodedMorse)
        ]
        return Outcome("".join(notations).strip(), tuple(self._decoder.records))

    @property
    def inter_char_threshold(self) -> float:
        return self._timing.inter_char_threshold

    def _pipeline(self) -> Pipeline:
        return Pipeline(
            source=self._source(),
            spectrum_analyzer=STFTSpectrumAnalyzer(
                SpectrumAnalyzerSettings(sample_rate=self._spec.sample_rate)
            ),
            spectrum_limiter=StaticSpectrumLimiter(SpectrumLimiterSettings()),
            carrier_source=PeakCarrierSource(CarrierSourceSettings()),
            noise_estimator=PercentileNoiseEstimator(NoiseEstimatorSettings()),
            keying_detector=AdaptiveKeyingDetector(KeyingDetectorSettings()),
            keying_debouncer=TimedKeyingDebouncer(self._case.debouncer),
            timing_decoder=self._decoder,
            interpreter=DummyInterpreter(InterpreterSettings()),
        )

    def _source(self) -> FileSource:
        return FileSource(
            self._spec.wav(),
            audio=AudioSettings(sample_rate=self._spec.sample_rate),
            decoder=SoundFileDecoder(),
            sample_clock=SampleClock(self._spec.sample_rate, _EPOCH),
        )
