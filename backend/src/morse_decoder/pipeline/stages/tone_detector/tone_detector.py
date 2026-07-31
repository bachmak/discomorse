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
from morse_decoder.pipeline.stages.tone_detector.impl.keying_detector import (
    AdaptiveKeyingDetector,
    KeyingDetector,
)
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    NoiseEstimator,
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class _SubstageConstructor[SubstageT](Protocol):
    def __call__(self, settings: ToneDetectorSettings) -> SubstageT: ...


_CARRIER_SOURCES: dict[str, _SubstageConstructor[CarrierSource]] = {
    "PeakCarrierSource": PeakCarrierSource,
}
_NOISE_ESTIMATORS: dict[str, _SubstageConstructor[NoiseEstimator]] = {
    "PercentileNoiseEstimator": PercentileNoiseEstimator,
}
_KEYING_DETECTORS: dict[str, _SubstageConstructor[KeyingDetector]] = {
    "AdaptiveKeyingDetector": AdaptiveKeyingDetector,
}


class SpectralToneDetector(ToneDetector):
    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._carrier_source = _build(
            _CARRIER_SOURCES, settings.carrier_source, "carrier source", settings
        )
        self._noise_estimator = _build(
            _NOISE_ESTIMATORS, settings.noise_estimator, "noise estimator", settings
        )
        self._keying_detector = _build(
            _KEYING_DETECTORS, settings.keying_detector, "keying detector", settings
        )

    async def process(self, reading: SpectrumReading) -> ToneReading:
        return ToneReading(
            samples=tuple(self._sample(spectrum) for spectrum in reading.spectrums)
        )

    def _sample(self, spectrum: ToneSpectrum) -> ToneSample:
        windowed = limit_to_window(spectrum, self._window)
        carrier = self._carrier_source.track(windowed)
        noise = self._noise_estimator.estimate(windowed)
        _ = self._keying_detector.detect(carrier, noise)
        return ToneSample(ts=spectrum.ts, on=False)


def _build[SubstageT](
    catalog: dict[str, _SubstageConstructor[SubstageT]],
    name: str,
    kind: str,
    settings: ToneDetectorSettings,
) -> SubstageT:
    return resolve(catalog, name, kind)(settings)
