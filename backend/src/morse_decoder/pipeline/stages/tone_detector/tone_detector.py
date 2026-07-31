from typing import Protocol

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import (
    SpectrumReading,
    ToneReading,
    ToneSample,
    ToneSpectrum,
)
from morse_decoder.pipeline.resolve_type import resolve
from morse_decoder.pipeline.stages.tone_detector.impl.carrier_source import (
    CarrierSource,
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import FrequencyWindow
from morse_decoder.pipeline.stages.tone_detector.impl.helpers import limit_to_window
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    NoiseEstimator,
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class _CarrierSourceConstructor(Protocol):
    def __call__(self, settings: ToneDetectorSettings) -> CarrierSource: ...


class _NoiseEstimatorConstructor(Protocol):
    def __call__(self, settings: ToneDetectorSettings) -> NoiseEstimator: ...


_CARRIER_SOURCES: dict[str, _CarrierSourceConstructor] = {
    "PeakCarrierSource": PeakCarrierSource,
}
_NOISE_ESTIMATORS: dict[str, _NoiseEstimatorConstructor] = {
    "PercentileNoiseEstimator": PercentileNoiseEstimator,
}


class SpectralToneDetector(ToneDetector):
    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._carrier_source = _build_carrier_source(settings)
        self._noise_estimator = _build_noise_estimator(settings)

    async def process(self, reading: SpectrumReading) -> ToneReading:
        return ToneReading(
            samples=tuple(self._sample(spectrum) for spectrum in reading.spectrums)
        )

    def _sample(self, spectrum: ToneSpectrum) -> ToneSample:
        windowed = limit_to_window(spectrum, self._window)
        _ = self._carrier_source.track(windowed)
        _ = self._noise_estimator.estimate(windowed)
        return ToneSample(ts=spectrum.ts, on=False)


def _build_carrier_source(settings: ToneDetectorSettings) -> CarrierSource:
    source = resolve(_CARRIER_SOURCES, settings.carrier_source, "carrier source")
    return source(settings)


def _build_noise_estimator(settings: ToneDetectorSettings) -> NoiseEstimator:
    estimator = resolve(_NOISE_ESTIMATORS, settings.noise_estimator, "noise estimator")
    return estimator(settings)
