from typing import Protocol

from morse_decoder.audio.source import AudioSource
from morse_decoder.config import (
    InterpreterSettings,
    PipelineSettings,
    SpectrumAnalyzerSettings,
    TimingDecoderSettings,
    ToneDetectorSettings,
)
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.pipeline.stages.interpreter.dummy_interpreter import DummyInterpreter
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)
from morse_decoder.pipeline.stages.timing_decoder.adaptive_threshold_decoder import (
    AdaptiveThresholdDecoder,
)
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder
from morse_decoder.pipeline.stages.tone_detector.dummy_tone_detector import (
    DummyToneDetector,
)
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class _SpectrumAnalyzerConstructor(Protocol):
    def __call__(self, settings: SpectrumAnalyzerSettings) -> SpectrumAnalyzer: ...


class _ToneDetectorConstructor(Protocol):
    def __call__(self, settings: ToneDetectorSettings) -> ToneDetector: ...


class _TimingDecoderConstructor(Protocol):
    def __call__(self, settings: TimingDecoderSettings) -> TimingDecoder: ...


class _InterpreterConstructor(Protocol):
    def __call__(self, settings: InterpreterSettings) -> Interpreter: ...


# We can't do mapping dict[str -> ToneDetector/TimingDecoder/etc] directly, because
# calling a constructor of an abstract class doesn't work and triggers type checks.
# That's why we introduced these proxy constructors.
_SPECTRUM_ANALYZERS: dict[str, _SpectrumAnalyzerConstructor] = {
    "STFTSpectrumAnalyzer": STFTSpectrumAnalyzer,
}
_TONE_DETECTORS: dict[str, _ToneDetectorConstructor] = {
    "DummyToneDetector": DummyToneDetector,
}
_TIMING_DECODERS: dict[str, _TimingDecoderConstructor] = {
    "AdaptiveThresholdDecoder": AdaptiveThresholdDecoder,
}
_INTERPRETERS: dict[str, _InterpreterConstructor] = {
    "DummyInterpreter": DummyInterpreter,
}


def _resolve[T](catalog: dict[str, T], name: str, kind: str) -> T:
    try:
        return catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc


def _build_spectrum_analyzer(settings: PipelineSettings) -> SpectrumAnalyzer:
    analyzer = _resolve(
        _SPECTRUM_ANALYZERS, settings.spectrum_analyzer, "spectrum analyzer"
    )
    return analyzer(settings.spectrum_analyzer_settings)


def _build_tone_detector(settings: PipelineSettings) -> ToneDetector:
    detector = _resolve(_TONE_DETECTORS, settings.tone_detector, "tone detector")
    return detector(settings.tone_detector_settings)


def _build_timing_decoder(settings: PipelineSettings) -> TimingDecoder:
    decoder = _resolve(_TIMING_DECODERS, settings.timing_decoder, "timing decoder")
    return decoder(settings.timing_decoder_settings)


def _build_interpreter(settings: PipelineSettings) -> Interpreter:
    interpreter = _resolve(_INTERPRETERS, settings.interpreter, "interpreter")
    return interpreter(settings.interpreter_settings)


def create_pipeline_runner(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> PipelineRunner:
    return PipelineRunner(
        source=source,
        spectrum_analyzer=_build_spectrum_analyzer(pipeline_settings),
        tone_detector=_build_tone_detector(pipeline_settings),
        timing_decoder=_build_timing_decoder(pipeline_settings),
        interpreter=_build_interpreter(pipeline_settings),
    )
