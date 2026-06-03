from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from morse_decoder.pipeline.types import MorseElement, ToneReading


class PluginConfig(BaseModel):
    """Base for a plugin's constructor configuration.

    `extra="forbid"` turns unknown keys (typos in config.toml) into validation
    errors instead of silently ignored settings; `frozen=True` keeps a built
    plugin's config immutable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class Plugin(ABC):
    """A pipeline component built from a typed, validated config object.

    A concrete plugin overrides `Config` with its own `PluginConfig` subclass
    and accepts an instance of it. Plugins that need no parameters inherit the
    empty default and are constructed from `{}`.
    """

    Config: ClassVar[type[PluginConfig]] = PluginConfig

    def __init__(self, config: PluginConfig) -> None:
        self._config = config


class ToneDetector(Plugin):
    @abstractmethod
    async def process(self, pcm: bytes) -> ToneReading:
        """Analyze one PCM chunk into a tone reading."""
        ...


class TimingDecoder(Plugin):
    @abstractmethod
    async def process(self, tone_on: bool, timestamp: float) -> list[MorseElement]:
        """Return the timing elements (dits, dahs, spaces) decoded at this instant."""
        ...


class Interpreter(Plugin):
    @abstractmethod
    async def interpret(self, elements: list[MorseElement]) -> str:
        """Render decoded elements into corrected, readable text."""
        ...
