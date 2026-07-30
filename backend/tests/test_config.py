import pytest
from pydantic import ValidationError

from morse_decoder.config import (
    AudioSettings,
    PipelineSettings,
    Settings,
    SpectrumAnalyzerSettings,
)


def _settings(audio_rate: int, analyzer_rate: int) -> Settings:
    return Settings(
        audio=AudioSettings(sample_rate=audio_rate),
        pipeline=PipelineSettings(
            spectrum_analyzer_settings=SpectrumAnalyzerSettings(
                sample_rate=analyzer_rate
            )
        ),
    )


@pytest.mark.parametrize(
    "sample_rate",
    [
        pytest.param(8_000, id="default-rate"),
        pytest.param(16_000, id="raised-rate"),
    ],
)
def test_settings_accept_agreeing_sample_rates(sample_rate: int) -> None:
    settings = _settings(sample_rate, sample_rate)

    assert settings.pipeline.spectrum_analyzer_settings.sample_rate == sample_rate


@pytest.mark.parametrize(
    "audio_rate, analyzer_rate",
    [
        pytest.param(16_000, 8_000, id="analyzer-lags-behind"),
        pytest.param(8_000, 44_100, id="analyzer-runs-ahead"),
    ],
)
def test_settings_reject_disagreeing_sample_rates(
    audio_rate: int, analyzer_rate: int
) -> None:
    with pytest.raises(ValidationError, match="must equal"):
        _settings(audio_rate, analyzer_rate)


def test_default_settings_agree_on_the_sample_rate() -> None:
    settings = Settings()

    assert (
        settings.audio.sample_rate
        == settings.pipeline.spectrum_analyzer_settings.sample_rate
    )
