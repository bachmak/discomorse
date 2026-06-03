from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000


class AudioSettings(BaseSettings):
    sample_rate: int = 8000
    chunk_size: int = 2048


class PipelineSettings(BaseSettings):
    tone_detector: str = "STFTDetector"
    timing_decoder: str = "AdaptiveThresholdDecoder"
    interpreter: str = "NoisyChannelInterpreter"
    language: str = "en"
    # Per-plugin parameters, keyed by stage. Each dict is validated against the
    # selected plugin's `Config` model before construction, so its keys must
    # match that model's fields; unknown keys or wrong types are rejected. IMMPROTANT
    tone_detector_config: dict[str, object] = Field(default_factory=dict)
    timing_decoder_config: dict[str, object] = Field(default_factory=dict)
    interpreter_config: dict[str, object] = Field(default_factory=dict)


class FFTSettings(BaseSettings):
    window_size: int = 512
    overlap: float = 0.5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file=["config.toml", "config.local.toml"],
        env_nested_delimiter="__",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    fft: FFTSettings = Field(default_factory=FFTSettings)


settings = Settings()
