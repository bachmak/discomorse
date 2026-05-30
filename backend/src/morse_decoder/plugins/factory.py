from morse_decoder.audio.base import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector

_tone_detectors: dict[str, type[ToneDetector]] = {}
_timing_decoders: dict[str, type[TimingDecoder]] = {}
_interpreters: dict[str, type[Interpreter]] = {}


def register_tone_detector(name: str) -> type:
    def decorator(cls: type[ToneDetector]) -> type[ToneDetector]:
        _tone_detectors[name] = cls
        return cls
    return decorator  # type: ignore[return-value]


def register_timing_decoder(name: str) -> type:
    def decorator(cls: type[TimingDecoder]) -> type[TimingDecoder]:
        _timing_decoders[name] = cls
        return cls
    return decorator  # type: ignore[return-value]


def register_interpreter(name: str) -> type:
    def decorator(cls: type[Interpreter]) -> type[Interpreter]:
        _interpreters[name] = cls
        return cls
    return decorator  # type: ignore[return-value]


def create_tone_detector(pipeline_settings: PipelineSettings) -> ToneDetector:
    name = pipeline_settings.tone_detector
    if name not in _tone_detectors:
        raise KeyError(f"Unknown tone detector: {name!r}")
    return _tone_detectors[name]()


def create_timing_decoder(pipeline_settings: PipelineSettings) -> TimingDecoder:
    name = pipeline_settings.timing_decoder
    if name not in _timing_decoders:
        raise KeyError(f"Unknown timing decoder: {name!r}")
    return _timing_decoders[name]()


def create_interpreter(pipeline_settings: PipelineSettings) -> Interpreter:
    name = pipeline_settings.interpreter
    if name not in _interpreters:
        raise KeyError(f"Unknown interpreter: {name!r}")
    return _interpreters[name]()


def create_pipeline_runner(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> PipelineRunner:
    return PipelineRunner(
        source=source,
        tone_detector=create_tone_detector(pipeline_settings),
        timing_decoder=create_timing_decoder(pipeline_settings),
        interpreter=create_interpreter(pipeline_settings),
    )
