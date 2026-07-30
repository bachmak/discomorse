from pydantic import Field
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
    pass


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
    tone_detector: str = "ThresholdToneDetector"
    timing_decoder: str = "AdaptiveThresholdDecoder"
    interpreter: str = "NoisyChannelInterpreter"
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
    fft: FFTSettings = Field(default_factory=FFTSettings)


global_settings = Settings()
