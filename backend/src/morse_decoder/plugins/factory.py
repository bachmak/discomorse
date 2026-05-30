from collections.abc import Callable

from morse_decoder.audio.base import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector


class Registry[T]:
    """Maps plugin names to classes: `register` is the decorator, `create` builds."""

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._classes: dict[str, type[T]] = {}

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        def decorator(cls: type[T]) -> type[T]:
            self._classes[name] = cls
            return cls

        return decorator

    def create(self, name: str) -> T:
        if name not in self._classes:
            raise KeyError(f"Unknown {self._kind}: {name!r}")
        return self._classes[name]()


_tone_detectors = Registry[ToneDetector]("tone detector")
_timing_decoders = Registry[TimingDecoder]("timing decoder")
_interpreters = Registry[Interpreter]("interpreter")

register_tone_detector = _tone_detectors.register
register_timing_decoder = _timing_decoders.register
register_interpreter = _interpreters.register


def create_pipeline_runner(
    source: AudioSource, pipeline_settings: PipelineSettings
) -> PipelineRunner:
    return PipelineRunner(
        source=source,
        tone_detector=_tone_detectors.create(pipeline_settings.tone_detector),
        timing_decoder=_timing_decoders.create(pipeline_settings.timing_decoder),
        interpreter=_interpreters.create(pipeline_settings.interpreter),
    )
