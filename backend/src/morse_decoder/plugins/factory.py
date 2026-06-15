from typing import Protocol

from morse_decoder.audio.base import AudioSource
from morse_decoder.config import (
    InterpreterSettings,
    PipelineSettings,
    TimingDecoderSettings,
    ToneDetectorSettings,
)
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector


class _ToneDetectorConstructor(Protocol):
    def __call__(self, settings: ToneDetectorSettings) -> ToneDetector: ...


class _TimingDecoderConstructor(Protocol):
    def __call__(self, settings: TimingDecoderSettings) -> TimingDecoder: ...


class _InterpreterConstructor(Protocol):
    def __call__(self, settings: InterpreterSettings) -> Interpreter: ...


# We can't do mapping dict[str -> ToneDetector/TimingDecoder/etc] directly, because
# calling a constructor of an abstract class doesn't work and triggers type checks.
# That's why we introduced these proxy constructors.
_TONE_DETECTORS: dict[str, _ToneDetectorConstructor] = {
    # "STFTDetector": STFTDetector,
}
_TIMING_DECODERS: dict[str, _TimingDecoderConstructor] = {
    # "AdaptiveThresholdDecoder": AdaptiveThresholdDecoder,
}
_INTERPRETERS: dict[str, _InterpreterConstructor] = {
    # "NoisyChannelInterpreter": NoisyChannelInterpreter,
}


def _resolve[T](catalog: dict[str, T], name: str, kind: str) -> T:
    try:
        return catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc


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
        tone_detector=_build_tone_detector(pipeline_settings),
        timing_decoder=_build_timing_decoder(pipeline_settings),
        interpreter=_build_interpreter(pipeline_settings),
    )
