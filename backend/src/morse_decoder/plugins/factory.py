from pydantic import ValidationError

from morse_decoder.audio.base import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import (
    Interpreter,
    Plugin,
    PluginConfig,
    TimingDecoder,
    ToneDetector,
)


class PluginConfigError(ValueError):
    """Raised when a plugin's config section fails validation."""

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


def _resolve[T: Plugin](
    catalog: dict[str, type[T]], name: str, kind: str
) -> type[T]:
    try:
        return catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc

# Validate the config for the selected plugin. Important because it catches typos and mistakes in the config file..
def _validate(
    cls: type[Plugin], name: str, kind: str, config: dict[str, object]
) -> PluginConfig:
    try:
        return cls.Config.model_validate(config)
    except ValidationError as exc:
        raise PluginConfigError(f"invalid config for {kind} {name!r}: {exc}") from exc


def _build[T: Plugin](
    catalog: dict[str, type[T]], name: str, kind: str, config: dict[str, object]
) -> T:
    cls = _resolve(catalog, name, kind)
    return cls(_validate(cls, name, kind, config))


def _build_tone_detector(settings: PipelineSettings) -> ToneDetector:
    return _build(
        _TONE_DETECTORS,
        settings.tone_detector,
        "tone detector",
        settings.tone_detector_config,
    )


def _build_timing_decoder(settings: PipelineSettings) -> TimingDecoder:
    return _build(
        _TIMING_DECODERS,
        settings.timing_decoder,
        "timing decoder",
        settings.timing_decoder_config,
    )


def _build_interpreter(settings: PipelineSettings) -> Interpreter:
    return _build(
        _INTERPRETERS,
        settings.interpreter,
        "interpreter",
        settings.interpreter_config,
    )


def create_pipeline_runner(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> PipelineRunner:
    return PipelineRunner(
        source=source,
        tone_detector=_build_tone_detector(pipeline_settings),
        timing_decoder=_build_timing_decoder(pipeline_settings),
        interpreter=_build_interpreter(pipeline_settings),
    )
