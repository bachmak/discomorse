from morse_decoder.audio.base import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector

# Concrete plugins are wired here explicitly.
# To add one: implement the class, import it above, and add a single entry to
# the matching table below. No decorators and no import-order rules — the
# factory simply knows its options.

_TONE_DETECTORS: dict[str, type[ToneDetector]] = {
    # "STFTDetector": STFTDetector,
}
_TIMING_DECODERS: dict[str, type[TimingDecoder]] = {
    # "AdaptiveThresholdDecoder": AdaptiveThresholdDecoder,
}
_INTERPRETERS: dict[str, type[Interpreter]] = {
    # "NoisyChannelInterpreter": NoisyChannelInterpreter,
}


def _resolve[T](catalog: dict[str, type[T]], name: str, kind: str) -> type[T]:
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
