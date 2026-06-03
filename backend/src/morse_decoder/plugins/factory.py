from morse_decoder.audio.base import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector

# Concrete plugins are wired here explicitly. 

## To add one: implement the class, import it above, and add a single entry to the matching table below. 
# No decorators and no import-order rules. The factory simply knows its options.

_TONE_DETECTORS: dict[str, type[ToneDetector]] = {
    # "STFTDetector": STFTDetector,
}
_TIMING_DECODERS: dict[str, type[TimingDecoder]] = {
    # "AdaptiveThresholdDecoder": AdaptiveThresholdDecoder,
}
_INTERPRETERS: dict[str, type[Interpreter]] = {
    # "NoisyChannelInterpreter": NoisyChannelInterpreter,
}


def _build[T](catalog: dict[str, type[T]], name: str, kind: str) -> T:
    try:
        cls = catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc
    return cls()


def create_pipeline_runner(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> PipelineRunner:
    return PipelineRunner(
        source=source,
        tone_detector=_build(
            _TONE_DETECTORS, pipeline_settings.tone_detector, "tone detector"
        ),
        timing_decoder=_build(
            _TIMING_DECODERS, pipeline_settings.timing_decoder, "timing decoder"
        ),
        interpreter=_build(
            _INTERPRETERS, pipeline_settings.interpreter, "interpreter"
        ),
    )
