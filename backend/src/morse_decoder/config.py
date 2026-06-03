from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000


class AudioSettings(BaseSettings):
    sample_rate: int = 8000
    chunk_size: int = 2048


# Per-plugin parameters get their own dedicated, strongly typed settings so the
# rest of the code receives validated objects instead of raw dicts. `extra=
# "forbid"` rejects unknown keys (typos) at load time. Concrete plugins declare
# the fields they need here and accept the matching type in their __init__.
class ToneDetectorSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")


class TimingDecoderSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")


class InterpreterSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")


class PipelineSettings(BaseSettings):
    tone_detector: str = "STFTDetector"
    timing_decoder: str = "AdaptiveThresholdDecoder"
    interpreter: str = "NoisyChannelInterpreter"
    language: str = "en"
    tone_detector_settings: ToneDetectorSettings = Field(
        default_factory=ToneDetectorSettings
    )
    timing_decoder_settings: TimingDecoderSettings = Field(
        default_factory=TimingDecoderSettings
    )
    interpreter_settings: InterpreterSettings = Field(
        default_factory=InterpreterSettings
    )


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
