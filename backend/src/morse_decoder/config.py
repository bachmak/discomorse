from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000


class AudioSettings(BaseSettings):
    sample_rate: int = 8000
    chunk_size: int = 2048


class SpectrumAnalyzerSettings(BaseSettings):
    sample_rate: int = 8000
    n_fft: int = 128
    hop_length: int = 16


class ToneDetectorSettings(BaseSettings):
    carrier_min_hz: float = Field(default=400.0, gt=0)
    carrier_max_hz: float = Field(default=1_200.0, gt=0)

    @model_validator(mode="after")
    def _carrier_window_must_rise(self) -> Self:
        if self.carrier_min_hz >= self.carrier_max_hz:
            raise ValueError(
                f"carrier_min_hz ({self.carrier_min_hz}) must be below "
                f"carrier_max_hz ({self.carrier_max_hz})"
            )
        return self


class TimingDecoderSettings(BaseSettings):
    seed_wpm: float = Field(default=20.0, gt=0)
    alpha: float = Field(default=0.2, gt=0, le=1)
    dah_threshold: float = Field(default=2.0, gt=1)
    inter_char_threshold: float = Field(default=2.0, gt=1)
    word_threshold: float = Field(default=5.0, gt=1)


class InterpreterSettings(BaseSettings):
    pass


class PipelineSettings(BaseSettings):
    spectrum_analyzer: str = "STFTSpectrumAnalyzer"
    tone_detector: str = "DummyToneDetector"
    timing_decoder: str = "AdaptiveThresholdDecoder"
    interpreter: str = "DummyInterpreter"
    language: str = "en"
    spectrum_analyzer_settings: SpectrumAnalyzerSettings = Field(
        default_factory=SpectrumAnalyzerSettings
    )
    tone_detector_settings: ToneDetectorSettings = Field(
        default_factory=ToneDetectorSettings
    )
    timing_decoder_settings: TimingDecoderSettings = Field(
        default_factory=TimingDecoderSettings
    )
    interpreter_settings: InterpreterSettings = Field(
        default_factory=InterpreterSettings
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file=["config.toml", "config.local.toml"],
        env_nested_delimiter="__",
        extra="forbid",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)

    # TODO: not the best way to achieve consistency
    # consider restructuring settings to only have one source of truth
    @model_validator(mode="after")
    def _sample_rates_must_agree(self) -> Self:
        common_rate = self.audio.sample_rate
        analyzer_rate = self.pipeline.spectrum_analyzer_settings.sample_rate
        if common_rate != analyzer_rate:
            raise ValueError(
                f"audio.sample_rate ({common_rate}) must equal "
                f"pipeline.spectrum_analyzer_settings.sample_rate ({analyzer_rate})"
            )
        return self


global_settings = Settings()
