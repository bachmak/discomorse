from typing import Protocol

from morse_decoder.audio.source import AudioSource
from morse_decoder.config import (
    CarrierSourceSettings,
    KeyingDebouncerSettings,
    KeyingDetectorSettings,
    NoiseEstimatorSettings,
    PipelineSettings,
    SpectrumAnalyzerSettings,
    SpectrumLimiterSettings,
    SymbolDecoderSettings,
    TextCorrectorSettings,
    TimingDecoderSettings,
)
from morse_decoder.pipeline.pipeline import Pipeline
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
from morse_decoder.pipeline.stages.carrier_source.peak_carrier_source import (
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer
from morse_decoder.pipeline.stages.keying_debouncer.timed_keying_debouncer import (
    TimedKeyingDebouncer,
)
from morse_decoder.pipeline.stages.keying_detector.adaptive_keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.keying_detector.interface import KeyingDetector
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator
from morse_decoder.pipeline.stages.noise_estimator.percentile_noise_estimator import (
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)
from morse_decoder.pipeline.stages.spectrum_limiter.interface import SpectrumLimiter
from morse_decoder.pipeline.stages.spectrum_limiter.static_spectrum_limiter import (
    StaticSpectrumLimiter,
)
from morse_decoder.pipeline.stages.symbol_decoder.dummy_symbol_decoder import (
    DummySymbolDecoder,
)
from morse_decoder.pipeline.stages.symbol_decoder.interface import SymbolDecoder
from morse_decoder.pipeline.stages.text_corrector.dummy_text_corrector import (
    DummyTextCorrector,
)
from morse_decoder.pipeline.stages.text_corrector.interface import TextCorrector
from morse_decoder.pipeline.stages.timing_decoder.adaptive_threshold_decoder import (
    AdaptiveThresholdDecoder,
)
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


class _StageConstructor[SettingsT, StageT](Protocol):
    def __call__(self, settings: SettingsT) -> StageT: ...


# We can't do mapping dict[str -> CarrierSource/TimingDecoder/etc] directly, because
# calling a constructor of an abstract class doesn't work and triggers type checks.
# That's why we introduced these proxy constructors.
_SPECTRUM_ANALYZERS: dict[
    str, _StageConstructor[SpectrumAnalyzerSettings, SpectrumAnalyzer]
] = {
    "STFTSpectrumAnalyzer": STFTSpectrumAnalyzer,
}
_SPECTRUM_LIMITERS: dict[
    str, _StageConstructor[SpectrumLimiterSettings, SpectrumLimiter]
] = {
    "StaticSpectrumLimiter": StaticSpectrumLimiter,
}
_CARRIER_SOURCES: dict[str, _StageConstructor[CarrierSourceSettings, CarrierSource]] = {
    "PeakCarrierSource": PeakCarrierSource,
}
_NOISE_ESTIMATORS: dict[
    str, _StageConstructor[NoiseEstimatorSettings, NoiseEstimator]
] = {
    "PercentileNoiseEstimator": PercentileNoiseEstimator,
}
_KEYING_DETECTORS: dict[
    str, _StageConstructor[KeyingDetectorSettings, KeyingDetector]
] = {
    "AdaptiveKeyingDetector": AdaptiveKeyingDetector,
}
_KEYING_DEBOUNCERS: dict[
    str, _StageConstructor[KeyingDebouncerSettings, KeyingDebouncer]
] = {
    "TimedKeyingDebouncer": TimedKeyingDebouncer,
}
_TIMING_DECODERS: dict[str, _StageConstructor[TimingDecoderSettings, TimingDecoder]] = {
    "AdaptiveThresholdDecoder": AdaptiveThresholdDecoder,
}
_SYMBOL_DECODERS: dict[str, _StageConstructor[SymbolDecoderSettings, SymbolDecoder]] = {
    "DummySymbolDecoder": DummySymbolDecoder,
}
_TEXT_CORRECTORS: dict[str, _StageConstructor[TextCorrectorSettings, TextCorrector]] = {
    "DummyTextCorrector": DummyTextCorrector,
}


def _resolve[T](catalog: dict[str, T], name: str, kind: str) -> T:
    """Pick the type a name stands for."""
    try:
        return catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc


def _build[SettingsT, StageT](
    catalog: dict[str, _StageConstructor[SettingsT, StageT]],
    name: str,
    kind: str,
    settings: SettingsT,
) -> StageT:
    return _resolve(catalog, name, kind)(settings)


def _build_spectrum_analyzer(settings: PipelineSettings) -> SpectrumAnalyzer:
    return _build(
        _SPECTRUM_ANALYZERS,
        settings.spectrum_analyzer,
        "spectrum analyzer",
        settings.spectrum_analyzer_settings,
    )


def _build_spectrum_limiter(settings: PipelineSettings) -> SpectrumLimiter:
    return _build(
        _SPECTRUM_LIMITERS,
        settings.spectrum_limiter,
        "spectrum limiter",
        settings.spectrum_limiter_settings,
    )


def _build_carrier_source(settings: PipelineSettings) -> CarrierSource:
    return _build(
        _CARRIER_SOURCES,
        settings.carrier_source,
        "carrier source",
        settings.carrier_source_settings,
    )


def _build_noise_estimator(settings: PipelineSettings) -> NoiseEstimator:
    return _build(
        _NOISE_ESTIMATORS,
        settings.noise_estimator,
        "noise estimator",
        settings.noise_estimator_settings,
    )


def _build_keying_detector(settings: PipelineSettings) -> KeyingDetector:
    return _build(
        _KEYING_DETECTORS,
        settings.keying_detector,
        "keying detector",
        settings.keying_detector_settings,
    )


def _build_keying_debouncer(settings: PipelineSettings) -> KeyingDebouncer:
    return _build(
        _KEYING_DEBOUNCERS,
        settings.keying_debouncer,
        "keying debouncer",
        settings.keying_debouncer_settings,
    )


def _build_timing_decoder(settings: PipelineSettings) -> TimingDecoder:
    return _build(
        _TIMING_DECODERS,
        settings.timing_decoder,
        "timing decoder",
        settings.timing_decoder_settings,
    )


def _build_symbol_decoder(settings: PipelineSettings) -> SymbolDecoder:
    return _build(
        _SYMBOL_DECODERS,
        settings.symbol_decoder,
        "symbol decoder",
        settings.symbol_decoder_settings,
    )


def _build_text_corrector(settings: PipelineSettings) -> TextCorrector:
    return _build(
        _TEXT_CORRECTORS,
        settings.text_corrector,
        "text corrector",
        settings.text_corrector_settings,
    )


def create_pipeline(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> Pipeline:
    return Pipeline(
        source=source,
        spectrum_analyzer=_build_spectrum_analyzer(pipeline_settings),
        spectrum_limiter=_build_spectrum_limiter(pipeline_settings),
        carrier_source=_build_carrier_source(pipeline_settings),
        noise_estimator=_build_noise_estimator(pipeline_settings),
        keying_detector=_build_keying_detector(pipeline_settings),
        keying_debouncer=_build_keying_debouncer(pipeline_settings),
        timing_decoder=_build_timing_decoder(pipeline_settings),
        symbol_decoder=_build_symbol_decoder(pipeline_settings),
        text_corrector=_build_text_corrector(pipeline_settings),
        stream_settings=pipeline_settings.stream_settings,
    )
