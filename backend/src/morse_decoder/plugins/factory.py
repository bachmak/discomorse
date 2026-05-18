from typing import TYPE_CHECKING

from morse_decoder.config import settings
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector

if TYPE_CHECKING:
    pass

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


def create_tone_detector() -> ToneDetector:
    name = settings.pipeline.tone_detector
    if name not in _tone_detectors:
        raise KeyError(f"Unknown tone detector: {name!r}")
    return _tone_detectors[name]()


def create_timing_decoder() -> TimingDecoder:
    name = settings.pipeline.timing_decoder
    if name not in _timing_decoders:
        raise KeyError(f"Unknown timing decoder: {name!r}")
    return _timing_decoders[name]()


def create_interpreter() -> Interpreter:
    name = settings.pipeline.interpreter
    if name not in _interpreters:
        raise KeyError(f"Unknown interpreter: {name!r}")
    return _interpreters[name]()
