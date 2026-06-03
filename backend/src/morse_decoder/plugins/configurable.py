from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, ValidationError


class PluginConfig(BaseModel):
    """Base for a plugin's constructor configuration.

    `extra="forbid"` turns unknown keys (typos in config.toml) into validation
    errors instead of silently ignored settings; `frozen=True` keeps a built
    plugin's config immutable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class PluginConfigError(ValueError):
    """Raised when a plugin's raw config fails validation."""


class Plugin:
    """A pipeline component built from a typed, validated config object.

    A concrete plugin overrides `Config` with its own `PluginConfig` subclass
    and accepts an instance of it. Plugins needing no parameters inherit the
    empty default and are built from `{}`. This class — not the behavioral
    interfaces in `base.py` — owns the construction/config concern.
    """

    Config: ClassVar[type[PluginConfig]] = PluginConfig

    def __init__(self, config: PluginConfig) -> None:
        self._config = config

    @classmethod
    def from_config(cls, raw: dict[str, object]) -> Self:
        """Parse raw settings into this plugin's typed config and build it.

        The single place where a raw config mapping becomes a validated
        `PluginConfig`; every other layer works with the typed object.
        """
        try:
            config = cls.Config.model_validate(raw)
        except ValidationError as exc:
            msg = f"invalid config for {cls.__name__}: {exc}"
            raise PluginConfigError(msg) from exc
        return cls(config)
