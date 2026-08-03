from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


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


class SpectrumLimiterSettings(BaseSettings):
    """The frequency band the stages behind the limiter get to read."""

    min_hz: float = Field(default=400.0, gt=0)
    max_hz: float = Field(default=1_200.0, gt=0)

    @model_validator(mode="after")
    def _band_must_rise(self) -> Self:
        if self.min_hz >= self.max_hz:
            raise ValueError(
                f"min_hz ({self.min_hz}) must be below max_hz ({self.max_hz})"
            )
        return self


class CarrierSourceSettings(BaseSettings):
    carrier_lock_magnitude: float = Field(default=0.05, gt=0)
    carrier_lock_tolerance_hz: float = Field(default=100.0, gt=0)
    carrier_lock_seconds: float = Field(default=0.02, gt=0)
    carrier_hold_seconds: float = Field(default=2.0, gt=0)


class NoiseEstimatorSettings(BaseSettings):
    noise_detector_percentile: float = Field(default=50.0, ge=0, le=100)


class KeyingDetectorSettings(BaseSettings):
    threshold_rise_alpha: float = Field(default=0.3, gt=0, le=1)
    threshold_fall_alpha: float = Field(default=0.05, gt=0, le=1)
    threshold_on_factor: float = Field(default=3.0, gt=1)
    threshold_off_factor: float = Field(default=1.5, gt=1)

    @model_validator(mode="after")
    def _keying_band_must_open(self) -> Self:
        if self.threshold_off_factor >= self.threshold_on_factor:
            raise ValueError(
                f"threshold_off_factor ({self.threshold_off_factor}) must be below "
                f"threshold_on_factor ({self.threshold_on_factor})"
            )
        return self


class KeyingDebouncerSettings(BaseSettings):
    debounce_rise_seconds: float = Field(default=0.004, ge=0)
    debounce_fall_seconds: float = Field(default=0.015, ge=0)

    @model_validator(mode="after")
    def _debounce_must_favour_the_key_down(self) -> Self:
        if self.debounce_rise_seconds > self.debounce_fall_seconds:
            raise ValueError(
                f"debounce_rise_seconds ({self.debounce_rise_seconds}) must not "
                f"exceed debounce_fall_seconds ({self.debounce_fall_seconds})"
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
    spectrum_limiter: str = "StaticSpectrumLimiter"
    carrier_source: str = "PeakCarrierSource"
    noise_estimator: str = "PercentileNoiseEstimator"
    keying_detector: str = "AdaptiveKeyingDetector"
    keying_debouncer: str = "TimedKeyingDebouncer"
    timing_decoder: str = "AdaptiveThresholdDecoder"
    interpreter: str = "DummyInterpreter"
    language: str = "en"
    spectrum_analyzer_settings: SpectrumAnalyzerSettings = Field(
        default_factory=SpectrumAnalyzerSettings
    )
    spectrum_limiter_settings: SpectrumLimiterSettings = Field(
        default_factory=SpectrumLimiterSettings
    )
    carrier_source_settings: CarrierSourceSettings = Field(
        default_factory=CarrierSourceSettings
    )
    noise_estimator_settings: NoiseEstimatorSettings = Field(
        default_factory=NoiseEstimatorSettings
    )
    keying_detector_settings: KeyingDetectorSettings = Field(
        default_factory=KeyingDetectorSettings
    )
    keying_debouncer_settings: KeyingDebouncerSettings = Field(
        default_factory=KeyingDebouncerSettings
    )
    timing_decoder_settings: TimingDecoderSettings = Field(
        default_factory=TimingDecoderSettings
    )
    interpreter_settings: InterpreterSettings = Field(
        default_factory=InterpreterSettings
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="forbid",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)

    # one source per file, highest priority first: pydantic-settings deep-merges
    # sources, while a single source with several files replaces whole sections
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, "config.local.toml"),
            TomlConfigSettingsSource(settings_cls, "config.toml"),
        )

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
